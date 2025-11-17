/**
 * Schedule Calendar Component - 14-day calendar view of upcoming schedule
 * 
 * Features:
 * - Visual calendar grid showing upcoming activities
 * - Color-coded by activity type (workout/meal)
 * - Shows completion status
 * - Click to view day details
 * - Customizable day range
 */

'use client';

import { useEffect, useState } from 'react';
import { useSchedule } from '@/hooks/use-schedule';
import type { ScheduleEntry } from '@/store/schedule-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { CheckCircle2, XCircle, Clock, Dumbbell, Utensils, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ScheduleCalendarProps {
  days?: number;
}

interface DaySchedule {
  date: string;
  entries: ScheduleEntry[];
  workoutCount: number;
  mealCount: number;
  completedCount: number;
  skippedCount: number;
}

export function ScheduleCalendar({ days = 14 }: ScheduleCalendarProps) {
  const { upcomingSchedule, upcomingLoading, upcomingError, fetchUpcomingSchedule } = useSchedule();
  const [currentDays, setCurrentDays] = useState(days);
  const [groupedSchedule, setGroupedSchedule] = useState<DaySchedule[]>([]);

  useEffect(() => {
    fetchUpcomingSchedule(currentDays);
  }, [currentDays, fetchUpcomingSchedule]);

  useEffect(() => {
    if (upcomingSchedule) {
      // Group entries by date
      const grouped = upcomingSchedule.entries.reduce((acc, entry) => {
        const existing = acc.find((d) => d.date === entry.entry_date);
        if (existing) {
          existing.entries.push(entry);
          if (entry.entry_type === 'workout') existing.workoutCount++;
          if (entry.entry_type === 'meal') existing.mealCount++;
          if (entry.completion_status === 'completed') existing.completedCount++;
          if (entry.completion_status === 'skipped') existing.skippedCount++;
        } else {
          acc.push({
            date: entry.entry_date,
            entries: [entry],
            workoutCount: entry.entry_type === 'workout' ? 1 : 0,
            mealCount: entry.entry_type === 'meal' ? 1 : 0,
            completedCount: entry.completion_status === 'completed' ? 1 : 0,
            skippedCount: entry.completion_status === 'skipped' ? 1 : 0,
          });
        }
        return acc;
      }, [] as DaySchedule[]);

      // Sort by date
      grouped.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      setGroupedSchedule(grouped);
    }
  }, [upcomingSchedule]);

  const handlePreviousWeek = () => {
    setCurrentDays((prev) => Math.max(7, prev - 7));
  };

  const handleNextWeek = () => {
    setCurrentDays((prev) => prev + 7);
  };

  const isToday = (dateString: string) => {
    const today = new Date().toISOString().split('T')[0];
    return dateString === today;
  };

  const isPast = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
  };

  const getCompletionRate = (day: DaySchedule) => {
    const total = day.entries.length;
    if (total === 0) return 0;
    return Math.round((day.completedCount / total) * 100);
  };

  if (upcomingLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2">
            {Array.from({ length: 14 }).map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (upcomingError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Schedule Calendar</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Error loading schedule: {upcomingError}</p>
        </CardContent>
      </Card>
    );
  }

  if (!upcomingSchedule || groupedSchedule.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Schedule Calendar</CardTitle>
          <CardDescription>Next {currentDays} days</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No scheduled activities in the next {currentDays} days.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Schedule Calendar</CardTitle>
            <CardDescription>
              {new Date(upcomingSchedule.start_date).toLocaleDateString()} -{' '}
              {new Date(upcomingSchedule.end_date).toLocaleDateString()}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={handlePreviousWeek}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleNextWeek}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 pb-4 border-b">
            <div>
              <div className="text-sm text-muted-foreground">Total Workouts</div>
              <div className="text-lg font-semibold">
                {groupedSchedule.reduce((sum, day) => sum + day.workoutCount, 0)}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Meals</div>
              <div className="text-lg font-semibold">
                {groupedSchedule.reduce((sum, day) => sum + day.mealCount, 0)}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Activities</div>
              <div className="text-lg font-semibold">
                {upcomingSchedule.entries.length}
              </div>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {groupedSchedule.map((day) => {
              const completionRate = getCompletionRate(day);
              const todayClass = isToday(day.date);
              const pastClass = isPast(day.date);

              return (
                <Card
                  key={day.date}
                  className={cn(
                    'cursor-pointer transition-all hover:shadow-md',
                    todayClass && 'ring-2 ring-primary',
                    pastClass && 'opacity-70'
                  )}

                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">
                          {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                        </CardTitle>
                        <CardDescription>
                          {new Date(day.date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </CardDescription>
                      </div>
                      {todayClass && (
                        <Badge variant="default" className="text-xs">
                          Today
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {/* Activity Counts */}
                    <div className="flex items-center gap-3 text-sm">
                      <div className="flex items-center gap-1">
                        <Dumbbell className="h-4 w-4 text-blue-500" />
                        <span>{day.workoutCount}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Utensils className="h-4 w-4 text-orange-500" />
                        <span>{day.mealCount}</span>
                      </div>
                    </div>

                    {/* Completion Status */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Progress</span>
                        <span className="font-medium">{completionRate}%</span>
                      </div>
                      <div className="h-2 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${completionRate}%` }}
                        />
                      </div>
                    </div>

                    {/* Status Badges */}
                    <div className="flex flex-wrap gap-1">
                      {day.completedCount > 0 && (
                        <Badge variant="default" className="text-xs bg-green-500">
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                          {day.completedCount}
                        </Badge>
                      )}
                      {day.skippedCount > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          <XCircle className="mr-1 h-3 w-3" />
                          {day.skippedCount}
                        </Badge>
                      )}
                      {day.entries.length - day.completedCount - day.skippedCount > 0 && (
                        <Badge variant="outline" className="text-xs">
                          <Clock className="mr-1 h-3 w-3" />
                          {day.entries.length - day.completedCount - day.skippedCount}
                        </Badge>
                      )}
                    </div>

                    {/* Entry List */}
                    <div className="space-y-1 pt-2 border-t">
                      {day.entries.slice(0, 3).map((entry) => (
                        <div
                          key={entry.id}
                          className="flex items-center justify-between text-xs text-muted-foreground"
                        >
                          <div className="flex items-center gap-1 truncate">
                            {entry.entry_type === 'workout' ? (
                              <Dumbbell className="h-3 w-3 text-blue-500 flex-shrink-0" />
                            ) : (
                              <Utensils className="h-3 w-3 text-orange-500 flex-shrink-0" />
                            )}
                            <span className="truncate">
                              {entry.workout?.name || entry.meal?.name || entry.entry_type}
                            </span>
                          </div>
                          {entry.completion_status === 'completed' && (
                            <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />
                          )}
                          {entry.completion_status === 'skipped' && (
                            <XCircle className="h-3 w-3 text-gray-400 flex-shrink-0" />
                          )}
                        </div>
                      ))}
                      {day.entries.length > 3 && (
                        <div className="text-xs text-muted-foreground">
                          +{day.entries.length - 3} more
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
