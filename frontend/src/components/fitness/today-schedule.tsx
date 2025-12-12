'use client';

import { useEffect, useState } from 'react';
import { useSchedule } from '@/hooks/use-schedule';
import type { ScheduleEntry } from '@/store/schedule-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Dumbbell, Utensils, CheckCircle2, XCircle, Clock } from 'lucide-react';
import Link from 'next/link';

export function TodaySchedule() {
  const { upcomingSchedule, upcomingLoading, upcomingError, fetchUpcomingSchedule } = useSchedule();
  const [dayEntries, setDayEntries] = useState<ScheduleEntry[]>([]);
  const today = new Date().toISOString().split('T')[0];

  useEffect(() => {
    fetchUpcomingSchedule(14);
  }, [fetchUpcomingSchedule]);

  useEffect(() => {
    if (upcomingSchedule) {
      const filtered = upcomingSchedule.entries.filter(entry => entry.entry_date === today);
      setDayEntries(filtered);
    }
  }, [upcomingSchedule, today]);

  const workouts = dayEntries.filter(e => e.entry_type === 'workout');
  const meals = dayEntries.filter(e => e.entry_type === 'meal');

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
      <Card>
        <CardHeader>
          <CardTitle>Today's Schedule</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (upcomingError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Today's Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Error loading schedule: {upcomingError}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle>Today's Schedule</CardTitle>
          <CardDescription>
            {dayEntries.length} {dayEntries.length === 1 ? 'activity' : 'activities'} scheduled
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Dumbbell className="h-4 w-4 text-blue-500" />
              Workouts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{workouts.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Utensils className="h-4 w-4 text-orange-500" />
              Meals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{meals.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {dayEntries.filter(e => e.completion_status === 'completed').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Workouts Section */}
      {workouts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
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
                          <CardTitle className="text-base">
                            {entry.workout_name || 'Workout'}
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
            <CardTitle className="text-lg flex items-center gap-2">
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
                          <CardTitle className="text-base">
                            {entry.meal_name || 'Meal'}
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
            <p className="text-muted-foreground">No activities scheduled for today.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
