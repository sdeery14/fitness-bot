'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useSchedule } from '@/hooks/use-schedule';
import type { ScheduleEntry } from '@/store/schedule-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, ChefHat, Clock, Package, AlertCircle } from 'lucide-react';

export default function MealPrepDetailPage() {
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
      if (found && found.entry_type === 'meal_prep') {
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

  if (upcomingError || !entry || !entry.prep_instructions) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8">
            <p className="text-destructive">Error loading meal prep session: {upcomingError || 'Not found'}</p>
            <Button onClick={() => router.back()} className="mt-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { prep_instructions } = entry;

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{prep_instructions.session_name}</h1>
          <p className="text-muted-foreground">{formatDate(entry.entry_date)}</p>
        </div>
        {getStatusBadge(entry.completion_status)}
      </div>

      {/* Session Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Duration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{prep_instructions.duration_minutes} min</p>
            {entry.entry_time && (
              <p className="text-sm text-muted-foreground">Start at {formatTime(entry.entry_time)}</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5" />
              Batch Size
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{prep_instructions.batch_size}</p>
            <p className="text-sm text-muted-foreground">servings</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ChefHat className="h-5 w-5" />
              Recipes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{prep_instructions.recipes.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Recipes */}
      {prep_instructions.recipes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ChefHat className="h-5 w-5" />
              Recipes to Prepare
            </CardTitle>
            <CardDescription>
              {prep_instructions.recipes.length} {prep_instructions.recipes.length === 1 ? 'recipe' : 'recipes'} for this session
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {prep_instructions.recipes.map((recipe, idx) => (
                <li key={idx} className="flex items-center gap-3 p-3 bg-secondary rounded-lg">
                  <Badge variant="outline" className="text-lg">{idx + 1}</Badge>
                  <span className="font-medium">{recipe}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Instructions */}
      {prep_instructions.instructions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Step-by-Step Instructions</CardTitle>
            <CardDescription>Follow these steps to complete your meal prep</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4">
              {prep_instructions.instructions.map((instruction, idx) => (
                <li key={idx} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold">
                      {idx + 1}
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <p className="text-base leading-relaxed">{instruction}</p>
                  </div>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {/* Storage Instructions */}
      {prep_instructions.storage_instructions && (
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-900">
              <Package className="h-5 w-5" />
              Storage Instructions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-amber-900 whitespace-pre-wrap">{prep_instructions.storage_instructions}</p>
          </CardContent>
        </Card>
      )}

      {/* Prep Notes */}
      {prep_instructions.notes && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Prep Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">{prep_instructions.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* User Notes */}
      {entry.user_notes && (
        <Card>
          <CardHeader>
            <CardTitle>Your Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">{entry.user_notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
