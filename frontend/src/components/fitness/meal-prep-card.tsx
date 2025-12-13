/**
 * Meal Prep Card Component - Displays meal prep session details
 * 
 * Features:
 * - Session name and duration
 * - Recipe list and batch size
 * - Step-by-step instructions
 * - Storage guidelines
 * - Completion tracking
 */

'use client';

import type { ScheduleEntry } from '@/store/schedule-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChefHat, CheckCircle2, XCircle, Clock, Timer, Package } from 'lucide-react';

interface MealPrepCardProps {
  entry: ScheduleEntry;
  showStatus?: boolean;
  compact?: boolean;
}

export function MealPrepCard({ entry, showStatus = true, compact = false }: MealPrepCardProps) {
  if (!entry.prep_instructions) {
    return null;
  }

  const { prep_instructions } = entry;

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

  if (compact) {
    return (
      <Card className="cursor-pointer hover:shadow-md transition-all">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(entry.completion_status)}
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <ChefHat className="h-4 w-4" />
                  {prep_instructions.session_name}
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
            <Timer className="inline h-3 w-3 mr-1" />
            {prep_instructions.duration_minutes} min • {prep_instructions.batch_size} servings
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
                <ChefHat className="h-5 w-5" />
                {prep_instructions.session_name}
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
        {/* Session Info */}
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <Timer className="h-4 w-4 text-blue-500" />
            <span>{prep_instructions.duration_minutes} minutes</span>
          </div>
          <div className="flex items-center gap-1">
            <Package className="h-4 w-4 text-purple-500" />
            <span>{prep_instructions.batch_size} servings</span>
          </div>
        </div>

        {/* Notes */}
        {prep_instructions.notes && (
          <div className="bg-blue-50 rounded-md p-3 text-sm text-blue-900">
            {prep_instructions.notes}
          </div>
        )}

        {/* Recipes */}
        <div>
          <h4 className="font-semibold text-sm mb-2">Recipes to Prep</h4>
          <ul className="space-y-1 ml-4">
            {prep_instructions.recipes.map((recipe, idx) => (
              <li key={idx} className="text-sm flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                {recipe}
              </li>
            ))}
          </ul>
        </div>

        {/* Instructions */}
        <div>
          <h4 className="font-semibold text-sm mb-2">Batch Cooking Steps</h4>
          <ol className="space-y-2">
            {prep_instructions.instructions.map((instruction, idx) => (
              <li key={idx} className="text-sm flex gap-3">
                <Badge variant="outline" className="h-5 px-2 flex-shrink-0">
                  {idx + 1}
                </Badge>
                <span className="flex-1">{instruction}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Storage Instructions */}
        <div className="bg-amber-50 rounded-md p-3">
          <h4 className="font-semibold text-sm text-amber-900 mb-1 flex items-center gap-2">
            <Package className="h-4 w-4" />
            Storage
          </h4>
          <p className="text-sm text-amber-900">{prep_instructions.storage_instructions}</p>
        </div>

        {/* User Notes */}
        {entry.user_notes && (
          <div className="border-t pt-3">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium">Notes:</span> {entry.user_notes}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
