/**
 * Grocery Shopping Card Component - Displays grocery shopping list entry
 * 
 * Features:
 * - Categorized grocery items (Produce, Meat, Dairy, etc.)
 * - Shopping date and time
 * - Completion tracking
 * - Optional notes
 */

'use client';

import type { ScheduleEntry, GroceryItem } from '@/store/schedule-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ShoppingCart, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface GroceryShoppingCardProps {
  entry: ScheduleEntry;
  showStatus?: boolean;
  compact?: boolean;
}

export function GroceryShoppingCard({ entry, showStatus = true, compact = false }: GroceryShoppingCardProps) {
  if (!entry.grocery_list) {
    return null;
  }

  const { grocery_list } = entry;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'skipped':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500">Completed</Badge>;
      case 'skipped':
        return <Badge variant="destructive">Skipped</Badge>;
      case 'rescheduled':
        return <Badge variant="secondary">Rescheduled</Badge>;
      default:
        return <Badge variant="outline">Scheduled</Badge>;
    }
  };

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

  if (compact) {
    return (
      <Card className="cursor-pointer hover:shadow-md transition-all">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(entry.completion_status)}
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <ShoppingCart className="h-4 w-4" />
                  Grocery Shopping
                </CardTitle>
                {entry.entry_time && (
                  <CardDescription className="text-sm">
                    {new Date(`2000-01-01T${entry.entry_time}`).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </CardDescription>
                )}
              </div>
            </div>
            {showStatus && getStatusBadge(entry.completion_status)}
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {grocery_list.items.length} items • {sortedCategories.length} categories
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="cursor-pointer hover:shadow-md transition-all">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getStatusIcon(entry.completion_status)}
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <ShoppingCart className="h-5 w-5" />
                Grocery Shopping
              </CardTitle>
              {entry.entry_time && (
                <CardDescription>
                  {new Date(`2000-01-01T${entry.entry_time}`).toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </CardDescription>
              )}
            </div>
          </div>
          {showStatus && getStatusBadge(entry.completion_status)}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Notes */}
        {grocery_list.notes && (
          <div className="bg-blue-50 rounded-md p-3 text-sm text-blue-900">
            {grocery_list.notes}
          </div>
        )}

        {/* Shopping List by Category */}
        <div className="space-y-4">
          {sortedCategories.map((category) => (
            <div key={category} className="space-y-2">
              <h4 className="font-semibold text-sm text-gray-700 uppercase tracking-wide">
                {category}
              </h4>
              <ul className="space-y-1.5 ml-4">
                {itemsByCategory[category].map((item, idx) => (
                  <li key={idx} className="flex items-start justify-between text-sm">
                    <div className="flex-1">
                      <span className="font-medium">{item.ingredient}</span>
                      {item.notes && (
                        <span className="text-muted-foreground ml-2">({item.notes})</span>
                      )}
                    </div>
                    <Badge variant="secondary" className="ml-2 text-xs">
                      {item.quantity}
                    </Badge>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* User Notes */}
        {entry.user_notes && (
          <div className="border-t pt-3">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium">Notes:</span> {entry.user_notes}
            </p>
          </div>
        )}

        {/* Item Count Summary */}
        <div className="border-t pt-3 text-sm text-muted-foreground">
          Total: {grocery_list.items.length} items across {sortedCategories.length} categories
        </div>
      </CardContent>
    </Card>
  );
}
