import React, { useRef } from 'react';
import { Editor } from '@tinymce/tinymce-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const RichTextEditor = ({ value, onChange, token, height = 400 }) => {
  const editorRef = useRef(null);

  const handleImageUpload = (blobInfo, progress) => new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('image', blobInfo.blob(), blobInfo.filename());

    axios.post(`${API}/upload/image`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (e) => {
        progress(e.loaded / e.total * 100);
      }
    })
    .then(response => {
      resolve(response.data.image_url);
    })
    .catch(error => {
      reject(error.response?.data?.detail || 'Image upload failed');
    });
  });

  const handleVideoUpload = (blobInfo, progress) => new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('video', blobInfo.blob(), blobInfo.filename());

    axios.post(`${API}/upload/video`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (e) => {
        progress(e.loaded / e.total * 100);
      }
    })
    .then(response => {
      resolve(response.data.video_url);
    })
    .catch(error => {
      reject(error.response?.data?.detail || 'Video upload failed');
    });
  });

  return (
    <div className="rich-text-editor">
      <Editor
        onInit={(evt, editor) => editorRef.current = editor}
        value={value}
        onEditorChange={(content, editor) => {
          onChange(content);
        }}
        init={{
          height: height,
          // Use GPL license for self-hosted version - no API key needed
          licenseKey: 'gpl',
          // Disable cloud features and API key validation
          promotion: false,
          upgrade_source: false,
          menubar: 'file edit view insert format tools table help',
          plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'help', 'wordcount'
          ],
          toolbar: 'undo redo | blocks | ' +
            'bold italic forecolor | alignleft aligncenter ' +
            'alignright alignjustify | bullist numlist outdent indent | ' +
            'removeformat | image media link | code fullscreen preview | help',
          content_style: `
            body { 
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
              font-size: 14px;
              background-color: #1a1a1a;
              color: #e5e5e5;
            }
            .mce-content-body {
              background-color: #1a1a1a !important;
              color: #e5e5e5 !important;
            }
          `,
          skin: 'oxide-dark',
          content_css: 'dark',
          images_upload_handler: handleImageUpload,
          file_picker_callback: function (callback, value, meta) {
            if (meta.filetype === 'image') {
              const input = document.createElement('input');
              input.setAttribute('type', 'file');
              input.setAttribute('accept', 'image/*');
              
              input.onchange = function () {
                const file = this.files[0];
                const formData = new FormData();
                formData.append('image', file);

                axios.post(`${API}/upload/image`, formData, {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                  }
                })
                .then(response => {
                  callback(response.data.image_url, { alt: file.name });
                })
                .catch(error => {
                  console.error('Image upload failed:', error);
                });
              };
              
              input.click();
            } else if (meta.filetype === 'media') {
              const input = document.createElement('input');
              input.setAttribute('type', 'file');
              input.setAttribute('accept', 'video/*');
              
              input.onchange = function () {
                const file = this.files[0];
                const formData = new FormData();
                formData.append('video', file);

                axios.post(`${API}/upload/video`, formData, {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                  }
                })
                .then(response => {
                  callback(response.data.video_url, { title: file.name });
                })
                .catch(error => {
                  console.error('Video upload failed:', error);
                });
              };
              
              input.click();
            }
          },
          media_alt_source: false,
          media_poster: false,
          media_dimensions: false,
          media_live_embeds: true,
          // YouTube and Vimeo embedding
          media_url_resolver: function (data, resolve) {
            if (data.url.indexOf('youtube.com') !== -1 || data.url.indexOf('youtu.be') !== -1) {
              const videoId = data.url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
              if (videoId) {
                resolve({
                  html: `<iframe width="560" height="315" src="https://www.youtube.com/embed/${videoId[1]}" frameborder="0" allowfullscreen></iframe>`
                });
              }
            } else if (data.url.indexOf('vimeo.com') !== -1) {
              const videoId = data.url.match(/vimeo\.com\/(\d+)/);
              if (videoId) {
                resolve({
                  html: `<iframe src="https://player.vimeo.com/video/${videoId[1]}" width="560" height="315" frameborder="0" allowfullscreen></iframe>`
                });
              }
            } else {
              resolve({ html: '' });
            }
          },
          // Custom styles for the barbershop theme
          formats: {
            barbershop_heading: {
              block: 'h2',
              styles: { 
                color: '#D4AF37',
                'font-family': 'serif',
                'font-weight': 'bold',
                'border-bottom': '2px solid #D4AF37',
                'padding-bottom': '10px',
                'margin-bottom': '20px'
              }
            },
            barbershop_quote: {
              block: 'blockquote',
              styles: {
                'border-left': '4px solid #D4AF37',
                'padding-left': '20px',
                'font-style': 'italic',
                'color': '#D4AF37',
                'background-color': 'rgba(212, 175, 55, 0.1)',
                'padding': '15px',
                'margin': '20px 0'
              }
            }
          },
          style_formats: [
            { title: 'Barbershop Heading', format: 'barbershop_heading' },
            { title: 'Barbershop Quote', format: 'barbershop_quote' },
            { title: 'Gold Text', inline: 'span', styles: { color: '#D4AF37' } },
            { title: 'Large Text', inline: 'span', styles: { 'font-size': '1.2em' } },
            { title: 'Small Text', inline: 'span', styles: { 'font-size': '0.9em' } }
          ]
        }}
      />
    </div>
  );
};

export default RichTextEditor;