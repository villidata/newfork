import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { 
  TrendingUp, 
  DollarSign, 
  Calendar, 
  Users, 
  BarChart3, 
  PieChart, 
  RefreshCw,
  AlertCircle,
  CheckCircle 
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const RevenueDashboard = ({ token, staff }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    period: 'monthly',
    staff_id: '',
    start_date: '',
    end_date: ''
  });

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError('');
      
      const params = new URLSearchParams();
      if (filters.period) params.append('period', filters.period);
      if (filters.staff_id) params.append('staff_id', filters.staff_id);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      
      const response = await axios.get(`${API}/analytics/revenue?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setError(error.response?.data?.detail || 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const applyFilters = () => {
    fetchAnalytics();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('da-DK', {
      style: 'currency',
      currency: 'DKK',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatPeriod = (period, type) => {
    if (type === 'daily') {
      return new Date(period).toLocaleDateString('da-DK');
    } else if (type === 'weekly') {
      const date = new Date(period);
      const endDate = new Date(date);
      endDate.setDate(date.getDate() + 6);
      return `${date.toLocaleDateString('da-DK')} - ${endDate.toLocaleDateString('da-DK')}`;
    } else if (type === 'monthly') {
      const [year, month] = period.split('-');
      return new Date(year, month - 1).toLocaleDateString('da-DK', { 
        year: 'numeric', 
        month: 'long' 
      });
    } else {
      return period;
    }
  };

  const getTrendIcon = (current, previous) => {
    if (current > previous) {
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    } else if (current < previous) {
      return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />;
    }
    return <TrendingUp className="h-4 w-4 text-gray-400" />;
  };

  if (loading && !analytics) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gold">Revenue Dashboard</h2>
        </div>
        <div className="text-center py-12">
          <RefreshCw className="h-8 w-8 text-gold animate-spin mx-auto mb-4" />
          <p className="text-gray-300">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Revenue Dashboard</h2>
        <Button 
          onClick={fetchAnalytics} 
          disabled={loading}
          className="bg-gold text-black hover:bg-gold/90"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card className="bg-gray-900/50 border-gold/20">
        <CardHeader>
          <CardTitle className="text-gold">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-gold">Period</Label>
              <Select value={filters.period} onValueChange={(value) => handleFilterChange('period', value)}>
                <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-gold/20">
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="yearly">Yearly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gold">Staff Member</Label>
              <Select value={filters.staff_id} onValueChange={(value) => handleFilterChange('staff_id', value)}>
                <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                  <SelectValue placeholder="All staff" />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-gold/20">
                  <SelectItem value="all">All Staff</SelectItem>
                  {staff.map(member => (
                    <SelectItem key={member.id} value={member.id}>
                      {member.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gold">Start Date</Label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                className="bg-black/50 border-gold/30 text-white"
              />
            </div>
            <div>
              <Label className="text-gold">End Date</Label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                className="bg-black/50 border-gold/30 text-white"
              />
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={applyFilters} className="bg-gold text-black hover:bg-gold/90">
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert className="border-red-500 bg-red-500/10">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <AlertDescription className="text-red-400">{error}</AlertDescription>
        </Alert>
      )}

      {analytics && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-gray-900/50 border-gold/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Total Revenue</p>
                    <p className="text-2xl font-bold text-gold">
                      {formatCurrency(analytics.summary.total_revenue)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-gold" />
                </div>
                <p className="text-gray-300 text-xs mt-2">
                  {analytics.summary.start_date} to {analytics.summary.end_date}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-900/50 border-gold/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Total Bookings</p>
                    <p className="text-2xl font-bold text-gold">
                      {analytics.summary.total_bookings}
                    </p>
                  </div>
                  <Calendar className="h-8 w-8 text-gold" />
                </div>
                <p className="text-gray-300 text-xs mt-2">
                  Confirmed & completed bookings
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-900/50 border-gold/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Average Booking Value</p>
                    <p className="text-2xl font-bold text-gold">
                      {formatCurrency(analytics.summary.average_booking_value)}
                    </p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-gold" />
                </div>
                <p className="text-gray-300 text-xs mt-2">
                  Per booking average
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Revenue Trend */}
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                Revenue Trend ({analytics.summary.period})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.revenue_by_period.length > 0 ? (
                  analytics.revenue_by_period.map((item, index) => {
                    const maxRevenue = Math.max(...analytics.revenue_by_period.map(p => p.revenue));
                    const widthPercentage = (item.revenue / maxRevenue) * 100;
                    
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300 font-medium">
                            {formatPeriod(item.period, analytics.summary.period)}
                          </span>
                          <div className="text-right">
                            <span className="text-gold font-bold">
                              {formatCurrency(item.revenue)}
                            </span>
                            <span className="text-gray-400 text-sm ml-2">
                              ({item.bookings} bookings)
                            </span>
                          </div>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-gold h-2 rounded-full transition-all duration-300"
                            style={{ width: `${widthPercentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-gray-400 text-center py-8">No revenue data available for this period</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Top Services */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-gray-900/50 border-gold/20">
              <CardHeader>
                <CardTitle className="text-gold flex items-center">
                  <PieChart className="h-5 w-5 mr-2" />
                  Top Services
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.top_services.length > 0 ? (
                    analytics.top_services.map((service, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <div>
                          <p className="text-white font-medium">{service.service_name}</p>
                          <p className="text-gray-400 text-sm">{service.bookings} bookings</p>
                        </div>
                        <p className="text-gold font-bold">
                          {formatCurrency(service.revenue)}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-400 text-center py-8">No service data available</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Staff Performance */}
            <Card className="bg-gray-900/50 border-gold/20">
              <CardHeader>
                <CardTitle className="text-gold flex items-center">
                  <Users className="h-5 w-5 mr-2" />
                  Staff Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.staff_performance.length > 0 ? (
                    analytics.staff_performance.map((staff, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="text-white font-medium">{staff.staff_name}</p>
                            <p className="text-gray-400 text-sm">
                              {staff.bookings} bookings • {formatCurrency(staff.average_per_booking)} avg
                            </p>
                          </div>
                          <p className="text-gold font-bold">
                            {formatCurrency(staff.revenue)}
                          </p>
                        </div>
                        {index < analytics.staff_performance.length - 1 && (
                          <div className="border-b border-gray-700"></div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-400 text-center py-8">No staff data available</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
};

export default RevenueDashboard;