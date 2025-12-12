'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useSchedule } from '@/hooks/use-schedule';
import type { ScheduleEntry } from '@/store/schedule-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Dumbbell, Utensils, CheckCircle2, XCircle, Clock } from 'lucide-react';
import Link from 'next/link';

export default function DayDetailPage() {
  const params = useParams();
  const router = useRouter();
  const date = params.date as string;
  const { upcomingSchedule, upcomingLoading, upcomingError, fetchUpcomingSchedule } = useSchedule();
  const [dayEntries, setDayEntries] = useState<ScheduleEntry[]>([]);

  useEffect(() => {
    fetchUpcomingSchedule(30); // Fetch more days to ensure we get the selected date
  }, [fetchUpcomingSchedule]);

  useEffect(() => {
    if (upcomingSchedule) {
      const filtered = upcomingSchedule.entries.filter(entry => entry.entry_date === date);
      setDayEntries(filtered);
    }
  }, [upcomingSchedule, date]);

  const workouts = dayEntries.filter(e => e.entry_type === 'workout');
  const meals = dayEntries.filter(e => e.entry_type === 'meal');

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'skipped':
        return <XCircle className="h-4 w-4 text-gray-400" />;
      default:
        return <Clock className="h-4 w-4 text-blue-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'skipped':
        return <Badge variant="secondary">Skipped</Badge>;
      default:
        return <Badge variant="outline">Scheduled</Badge>;
    }
  };

  if (upcomingLoading) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (upcomingError) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8">
            <p className="text-destructive">Error loading schedule: {upcomingError}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{formatDate(date)}</h1>
        <p className="text-muted-foreground">
          {dayEntries.length} {dayEntries.length === 1 ? 'activity' : 'activities'} scheduled
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Dumbbell className="h-5 w-5 text-blue-500" />
              Workouts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{workouts.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Utensils className="h-5 w-5 text-orange-500" />
              Meals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{meals.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {dayEntries.filter(e => e.completion_status === 'completed').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Workouts Section */}
      {workouts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Dumbbell className="h-5 w-5" />
              Workouts
            </CardTitle>
            <CardDescription>{workouts.length} workout{workouts.length !== 1 ? 's' : ''} scheduled</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {workouts.map((entry) => (
              <Link
                key={entry.id}
                href={`/dashboard/schedule/workout/${entry.workout_id}`}
                className="block"
              >
                <Card className="cursor-pointer hover:shadow-md transition-all">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(entry.completion_status)}
                        <div>
                          <CardTitle className="text-lg">
                            {entry.workout_name || 'Workout'}
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
                      {getStatusBadge(entry.completion_status)}
                    </div>
                  </CardHeader>
                  {entry.user_notes && (
                    <CardContent>
                      <p className="text-sm text-muted-foreground">{entry.user_notes}</p>
                    </CardContent>
                  )}
                </Card>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Meals Section */}
      {meals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Utensils className="h-5 w-5" />
              Meals
            </CardTitle>
            <CardDescription>{meals.length} meal{meals.length !== 1 ? 's' : ''} planned</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {meals.map((entry) => (
              <Link
                key={entry.id}
                href={`/dashboard/schedule/meal/${entry.meal_id}`}
                className="block"
              >
                <Card className="cursor-pointer hover:shadow-md transition-all">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(entry.completion_status)}
                        <div>
                          <CardTitle className="text-lg">
                            {entry.meal_name || 'Meal'}
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
                      {getStatusBadge(entry.completion_status)}
                    </div>
                  </CardHeader>
                  {entry.user_notes && (
                    <CardContent>
                      <p className="text-sm text-muted-foreground">{entry.user_notes}</p>
                    </CardContent>
                  )}
                </Card>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}

      {dayEntries.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No activities scheduled for this day.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
