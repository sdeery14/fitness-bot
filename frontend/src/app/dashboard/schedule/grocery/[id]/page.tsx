'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useSchedule } from '@/hooks/use-schedule';
import type { ScheduleEntry, GroceryItem } from '@/store/schedule-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, ShoppingCart, CheckCircle2, Clock, Package } from 'lucide-react';

export default function GroceryShoppingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const entryId = params.id as string;
  const { upcomingSchedule, upcomingLoading, upcomingError, fetchUpcomingSchedule } = useSchedule();
  const [entry, setEntry] = useState<ScheduleEntry | null>(null);

  useEffect(() => {
    fetchUpcomingSchedule(60); // Fetch enough days to find the entry
  }, [fetchUpcomingSchedule]);

  useEffect(() => {
    if (upcomingSchedule) {
      const found = upcomingSchedule.entries.find(e => e.id === entryId);
      if (found && found.entry_type === 'grocery_shopping') {
        setEntry(found);
      }
    }
  }, [upcomingSchedule, entryId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (timeString?: string) => {
    if (!timeString) return null;
    return new Date(`2000-01-01T${timeString}`).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'skipped':
        return <Badge variant="destructive">Skipped</Badge>;
      case 'rescheduled':
        return <Badge variant="secondary">Rescheduled</Badge>;
      default:
        return <Badge variant="outline">Scheduled</Badge>;
    }
  };

  if (upcomingLoading) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (upcomingError || !entry || !entry.grocery_list) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8">
            <p className="text-destructive">Error loading grocery shopping trip: {upcomingError || 'Not found'}</p>
            <Button onClick={() => router.back()} className="mt-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { grocery_list } = entry;

  // Group items by category
  const itemsByCategory = grocery_list.items.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = [];
    }
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, GroceryItem[]>);

  const categoryOrder = ['Produce', 'Meat', 'Dairy', 'Grains', 'Frozen', 'Pantry', 'Other'];
  const sortedCategories = Object.keys(itemsByCategory).sort((a, b) => {
    const aIndex = categoryOrder.indexOf(a);
    const bIndex = categoryOrder.indexOf(b);
    if (aIndex === -1 && bIndex === -1) return a.localeCompare(b);
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });

  const totalItems = grocery_list.items.length;
  const completedItems = grocery_list.items.filter(item => item.purchased).length;

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Grocery Shopping Trip</h1>
          <p className="text-muted-foreground">{formatDate(entry.entry_date)}</p>
        </div>
        {getStatusBadge(entry.completion_status)}
      </div>

      {/* Trip Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{formatTime(entry.entry_time) || 'Any time'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShoppingCart className="h-5 w-5" />
              Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{totalItems}</p>
            <p className="text-sm text-muted-foreground">{completedItems} purchased</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5" />
              Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{sortedCategories.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Shopping Notes */}
      {grocery_list.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Shopping Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">{grocery_list.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Grocery List by Category */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5" />
            Shopping List
          </CardTitle>
          <CardDescription>
            {totalItems} items across {sortedCategories.length} categories
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {sortedCategories.map((category) => (
              <div key={category}>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  {category}
                  <Badge variant="secondary" className="ml-auto">
                    {itemsByCategory[category].length} items
                  </Badge>
                </h3>
                <div className="space-y-2">
                  {itemsByCategory[category].map((item, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        item.purchased
                          ? 'bg-green-50 border-green-200 text-green-900'
                          : 'bg-white border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {item.purchased && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                        <div>
                          <p className={`font-medium ${item.purchased ? 'line-through' : ''}`}>
                            {item.ingredient}
                          </p>
                          {item.notes && (
                            <p className="text-sm text-muted-foreground">{item.notes}</p>
                          )}
                        </div>
                      </div>
                      <p className="font-semibold">{item.quantity}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* User Notes */}
      {entry.user_notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">{entry.user_notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
