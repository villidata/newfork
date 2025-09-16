import React, { useState } from 'react';
import { 
  Scissors, 
  User, 
  Star, 
  Crown, 
  Palette, 
  Sparkles, 
  Heart, 
  Award,
  Zap,
  Gem,
  Flame,
  Target,
  CheckCircle,
  ThumbsUp,
  Coffee,
  Clock,
  Calendar,
  DollarSign,
  Gift,
  Smile
} from 'lucide-react';
import { 
  GiRazor,
  GiComb,
  GiMustache,
  GiBeard,
  GiCurlyHair,
  GiHairStrands,
  GiScissors,
  GiSpray,
  GiHotSurface
} from 'react-icons/gi';
import { 
  FaCut,
  FaSprayCan,
  FaPaintBrush,
  FaUserTie,
  FaMale,
  FaChild
} from 'react-icons/fa';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

const IconSelector = ({ selectedIcon, onIconSelect, className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);

  const iconCategories = {
    "Barbershop Essentials": [
      { icon: <Scissors className="h-6 w-6" />, value: "scissors", name: "Scissors" },
      { icon: <GiRazor className="h-6 w-6" />, value: "razor", name: "Razor" },
      { icon: <GiComb className="h-6 w-6" />, value: "comb", name: "Comb" },
      { icon: <GiScissors className="h-6 w-6" />, value: "barber-scissors", name: "Barber Scissors" },
      { icon: <GiMirror className="h-6 w-6" />, value: "mirror", name: "Mirror" },
      { icon: <FaCut className="h-6 w-6" />, value: "cut", name: "Cut" }
    ],
    "Hair & Styling": [
      { icon: <GiCurlyHair className="h-6 w-6" />, value: "curly-hair", name: "Curly Hair" },
      { icon: <GiHairStrands className="h-6 w-6" />, value: "hair-strands", name: "Hair Strands" },
      { icon: <GiSpray className="h-6 w-6" />, value: "spray", name: "Hair Spray" },
      { icon: <FaSprayCan className="h-6 w-6" />, value: "spray-can", name: "Spray Can" },
      { icon: <FaPaintBrush className="h-6 w-6" />, value: "paint-brush", name: "Color Brush" },
      { icon: <Palette className="h-6 w-6" />, value: "palette", name: "Color Palette" }
    ],
    "Facial Hair": [
      { icon: <GiMustache className="h-6 w-6" />, value: "mustache", name: "Mustache" },
      { icon: <GiBeard className="h-6 w-6" />, value: "beard", name: "Beard" }
    ],
    "Client Types": [
      { icon: <User className="h-6 w-6" />, value: "user", name: "Adult" },
      { icon: <FaMale className="h-6 w-6" />, value: "male", name: "Men" },
      { icon: <FaChild className="h-6 w-6" />, value: "child", name: "Kids" },
      { icon: <FaUserTie className="h-6 w-6" />, value: "user-tie", name: "Professional" }
    ],
    "Premium & Special": [
      { icon: <Crown className="h-6 w-6" />, value: "crown", name: "Premium" },
      { icon: <Star className="h-6 w-6" />, value: "star", name: "Star" },
      { icon: <Award className="h-6 w-6" />, value: "award", name: "Award" },
      { icon: <Gem className="h-6 w-6" />, value: "gem", name: "Diamond" },
      { icon: <Sparkles className="h-6 w-6" />, value: "sparkles", name: "Sparkles" },
      { icon: <Flame className="h-6 w-6" />, value: "flame", name: "Hot" },
      { icon: <Zap className="h-6 w-6" />, value: "zap", name: "Express" }
    ],
    "Service Quality": [
      { icon: <Heart className="h-6 w-6" />, value: "heart", name: "Loved" },
      { icon: <ThumbsUp className="h-6 w-6" />, value: "thumbs-up", name: "Recommended" },
      { icon: <CheckCircle className="h-6 w-6" />, value: "check-circle", name: "Quality" },
      { icon: <Target className="h-6 w-6" />, value: "target", name: "Precision" },
      { icon: <Gift className="h-6 w-6" />, value: "gift", name: "Special Offer" },
      { icon: <Smile className="h-6 w-6" />, value: "smile", name: "Happy Client" }
    ],
    "Business": [
      { icon: <Clock className="h-6 w-6" />, value: "clock", name: "Quick Service" },
      { icon: <Calendar className="h-6 w-6" />, value: "calendar", name: "Appointment" },
      { icon: <DollarSign className="h-6 w-6" />, value: "dollar", name: "Pricing" },
      { icon: <Coffee className="h-6 w-6" />, value: "coffee", name: "Relaxing" }
    ]
  };

  const emojiIcons = [
    { emoji: "✂️", value: "scissors-emoji", name: "Scissors" },
    { emoji: "🪒", value: "razor-emoji", name: "Razor" },
    { emoji: "💇‍♂️", value: "haircut-man", name: "Men's Haircut" },
    { emoji: "💇‍♀️", value: "haircut-woman", name: "Women's Haircut" },
    { emoji: "💆‍♂️", value: "massage-man", name: "Men's Treatment" },
    { emoji: "💆‍♀️", value: "massage-woman", name: "Women's Treatment" },
    { emoji: "🧔", value: "beard-emoji", name: "Beard" },
    { emoji: "👨‍🦲", value: "bald-man", name: "Bald Style" },
    { emoji: "💄", value: "makeup", name: "Makeup" },
    { emoji: "🌟", value: "star-emoji", name: "Star" },
    { emoji: "⭐", value: "star-filled", name: "Premium" },
    { emoji: "✨", value: "sparkles-emoji", name: "Sparkles" },
    { emoji: "💎", value: "diamond-emoji", name: "Diamond" },
    { emoji: "👑", value: "crown-emoji", name: "Royal" },
    { emoji: "🔥", value: "fire-emoji", name: "Hot" },
    { emoji: "⚡", value: "lightning", name: "Fast" },
    { emoji: "💧", value: "water-drop", name: "Styling" },
    { emoji: "🎨", value: "art", name: "Creative" },
    { emoji: "💯", value: "hundred", name: "Perfect" },
    { emoji: "❤️", value: "heart-emoji", name: "Love" }
  ];

  const getCurrentIcon = () => {
    // First check emoji icons
    const emojiIcon = emojiIcons.find(icon => icon.value === selectedIcon);
    if (emojiIcon) {
      return <span className="text-2xl">{emojiIcon.emoji}</span>;
    }

    // Then check component icons
    for (const category of Object.values(iconCategories)) {
      const icon = category.find(icon => icon.value === selectedIcon);
      if (icon) {
        return React.cloneElement(icon.icon, { className: "h-6 w-6 text-gold" });
      }
    }

    // Default fallback
    return <Sparkles className="h-6 w-6 text-gold" />;
  };

  return (
    <div className={`relative ${className}`}>
      <div className="mb-2">
        <label className="block text-sm font-medium text-gold mb-1">Service Icon</label>
        <Button
          type="button"
          variant="outline"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full justify-start bg-black/50 border-gold/30 text-white hover:bg-gold/10"
        >
          <div className="flex items-center gap-2">
            {getCurrentIcon()}
            <span>Select Icon</span>
          </div>
        </Button>
      </div>

      {isOpen && (
        <Card className="absolute z-50 w-full max-w-2xl bg-gray-900 border-gold/20 shadow-xl max-h-96 overflow-y-auto">
          <CardContent className="p-4">
            <div className="space-y-4">
              {/* Emoji Icons Section */}
              <div>
                <h4 className="text-sm font-medium text-gold mb-2">Emoji Icons</h4>
                <div className="grid grid-cols-8 gap-2">
                  {emojiIcons.map((icon) => (
                    <button
                      key={icon.value}
                      type="button"
                      onClick={() => {
                        onIconSelect(icon.value);
                        setIsOpen(false);
                      }}
                      className={`p-2 rounded-md text-center hover:bg-gold/20 transition-colors ${
                        selectedIcon === icon.value ? 'bg-gold/30 ring-2 ring-gold' : 'bg-black/30'
                      }`}
                      title={icon.name}
                    >
                      <span className="text-xl">{icon.emoji}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Component Icons Sections */}
              {Object.entries(iconCategories).map(([categoryName, icons]) => (
                <div key={categoryName}>
                  <h4 className="text-sm font-medium text-gold mb-2">{categoryName}</h4>
                  <div className="grid grid-cols-6 gap-2">
                    {icons.map((icon) => (
                      <button
                        key={icon.value}
                        type="button"
                        onClick={() => {
                          onIconSelect(icon.value);
                          setIsOpen(false);
                        }}
                        className={`p-3 rounded-md flex items-center justify-center hover:bg-gold/20 transition-colors ${
                          selectedIcon === icon.value ? 'bg-gold/30 ring-2 ring-gold' : 'bg-black/30'
                        }`}
                        title={icon.name}
                      >
                        <div className="text-gold">
                          {icon.icon}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default IconSelector;