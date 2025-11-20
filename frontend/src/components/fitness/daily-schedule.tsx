/**
 * Daily Schedule Component - Displays today's workouts and meals in a timeline view
 * 
 * Features:
 * - Timeline view of today's scheduled activities
 * - Mark workouts/meals as complete
 * - Skip activities with reason
 * - Show completion status
 * - Display summary statistics
 */

'use client';

import { useEffect, useState } from 'react';
import { useSchedule } from '@/hooks/use-schedule';
import type { ScheduleEntry } from '@/store/schedule-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { CheckCircle2, XCircle, Clock, Utensils, Dumbbell } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

export function DailySchedule() {
  const { todaySchedule, todayLoading, todayError, fetchTodaySchedule, markComplete, skipEntry } =
    useSchedule();

  const [selectedEntry, setSelectedEntry] = useState<ScheduleEntry | null>(null);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [showSkipDialog, setShowSkipDialog] = useState(false);
  const [notes, setNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchTodaySchedule();
  }, [fetchTodaySchedule]);

  const handleComplete = async () => {
    if (!selectedEntry) return;

    setActionLoading(true);
    try {
      await markComplete(selectedEntry.id, notes);
      setShowCompleteDialog(false);
      setSelectedEntry(null);
      setNotes('');
    } catch (error) {
      console.error('Failed to mark complete:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSkip = async () => {
    if (!selectedEntry) return;

    setActionLoading(true);
    try {
      await skipEntry(selectedEntry.id, notes);
      setShowSkipDialog(false);
      setSelectedEntry(null);
      setNotes('');
    } catch (error) {
      console.error('Failed to skip entry:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: ScheduleEntry['completion_status']) => {
    switch (status) {
      case 'completed':
        return (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle2 className="mr-1 h-3 w-3" />
            Completed
          </Badge>
        );
      case 'skipped':
        return (
          <Badge variant="secondary">
            <XCircle className="mr-1 h-3 w-3" />
            Skipped
          </Badge>
        );
      case 'scheduled':
        return (
          <Badge variant="outline">
            <Clock className="mr-1 h-3 w-3" />
            Scheduled
          </Badge>
        );
      default:
        return null;
    }
  };

  const getIcon = (type: 'workout' | 'meal') => {
    return type === 'workout' ? (
      <Dumbbell className="h-5 w-5 text-blue-500" />
    ) : (
      <Utensils className="h-5 w-5 text-orange-500" />
    );
  };

  if (todayLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (todayError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Today&apos;s Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Error loading schedule: {todayError}</p>
        </CardContent>
      </Card>
    );
  }

  if (!todaySchedule || todaySchedule.entries.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Today&apos;s Schedule</CardTitle>
          <CardDescription>
            {mounted ? new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : ''}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No activities scheduled for today. Enjoy your rest day!</p>
        </CardContent>
      </Card>
    );
  }

  const { entries, summary } = todaySchedule;
  const completionRate = summary.total_workouts + summary.total_meals > 0
    ? Math.round(
        ((summary.completed_workouts + summary.completed_meals) /
          (summary.total_workouts + summary.total_meals)) *
          100
      )
    : 0;

  return (
    <>
      <Card role="region" aria-labelledby="daily-schedule-title">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle id="daily-schedule-title">Today&apos;s Schedule</CardTitle>
              <CardDescription>
                {mounted ? new Date(todaySchedule.date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                }) : ''}
              </CardDescription>
            </div>
            <div className="text-right">
              <div 
                className="text-2xl font-bold" 
                role="status" 
                aria-live="polite"
                aria-label={`${completionRate}% of today's activities completed`}
              >
                {completionRate}%
              </div>
              <div className="text-sm text-muted-foreground" aria-hidden="true">Completed</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4 pb-4 border-b" role="group" aria-label="Activity summary">
              <div>
                <div className="text-sm text-muted-foreground">Workouts</div>
                <div className="text-lg font-semibold" aria-label={`${summary.completed_workouts} of ${summary.total_workouts} workouts completed`}>
                  {summary.completed_workouts} / {summary.total_workouts}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Meals</div>
                <div className="text-lg font-semibold" aria-label={`${summary.completed_meals} of ${summary.total_meals} meals completed`}>
                  {summary.completed_meals} / {summary.total_meals}
                </div>
              </div>
            </div>

            {/* Schedule Entries */}
            <div className="space-y-3" role="list" aria-label="Today's activities">
              {entries.map((entry) => {
                const activityName = entry.workout?.name || entry.meal?.name || entry.entry_type;
                
                return (
                  <Card 
                    key={entry.id} 
                    className="border-l-4" 
                    style={{
                      borderLeftColor: entry.entry_type === 'workout' ? '#3b82f6' : '#f97316'
                    }}
                    role="listitem"
                    aria-labelledby={`entry-${entry.id}-title`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          {getIcon(entry.entry_type)}
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold" id={`entry-${entry.id}-title`}>
                                {activityName}
                              </h4>
                              {getStatusBadge(entry.completion_status)}
                            </div>
                            {entry.entry_time && (
                              <p className="text-sm text-muted-foreground mt-1">
                                <span className="sr-only">Scheduled time: </span>
                                {new Date(`2000-01-01T${entry.entry_time}`).toLocaleTimeString('en-US', {
                                  hour: 'numeric',
                                  minute: '2-digit',
                                })}
                              </p>
                            )}
                            {(entry.workout?.description || entry.meal?.description) && (
                              <p className="text-sm text-muted-foreground mt-2">
                                {entry.workout?.description || entry.meal?.description}
                              </p>
                            )}
                            {entry.user_notes && (
                              <p className="text-sm italic text-muted-foreground mt-2">
                                <span className="sr-only">User note: </span>
                                Note: {entry.user_notes}
                              </p>
                            )}
                          </div>
                        </div>
                        {entry.completion_status === 'scheduled' && (
                          <div className="flex gap-2" role="group" aria-label={`Actions for ${activityName}`}>
                            <Button
                              size="sm"
                              onClick={() => {
                                setSelectedEntry(entry);
                                setShowCompleteDialog(true);
                              }}
                              aria-label={`Mark ${activityName} as complete`}
                            >
                              Complete
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedEntry(entry);
                                setShowSkipDialog(true);
                              }}
                              aria-label={`Skip ${activityName}`}
                            >
                              Skip
                            </Button>
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

      {/* Complete Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent aria-describedby="complete-dialog-description">
          <DialogHeader>
            <DialogTitle>Mark as Complete</DialogTitle>
            <DialogDescription id="complete-dialog-description">
              Add any notes about this {selectedEntry?.entry_type} (optional)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="complete-notes">Notes</Label>
              <Textarea
                id="complete-notes"
                placeholder="How did it go? Any observations?"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                aria-label="Activity completion notes"
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowCompleteDialog(false)}
              aria-label="Cancel marking activity as complete"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleComplete} 
              disabled={actionLoading}
              aria-label={actionLoading ? 'Saving...' : 'Confirm marking activity as complete'}
            >
              {actionLoading ? 'Saving...' : 'Complete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Skip Dialog */}
      <Dialog open={showSkipDialog} onOpenChange={setShowSkipDialog}>
        <DialogContent aria-describedby="skip-dialog-description">
          <DialogHeader>
            <DialogTitle>Skip Activity</DialogTitle>
            <DialogDescription id="skip-dialog-description">
              Please provide a reason for skipping this {selectedEntry?.entry_type}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="skip-reason">Reason (required)</Label>
              <Textarea
                id="skip-reason"
                placeholder="e.g., Not feeling well, Time constraints, etc."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                required
                aria-required="true"
                aria-label="Reason for skipping activity"
                aria-invalid={!notes.trim()}
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowSkipDialog(false)}
              aria-label="Cancel skipping activity"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSkip} 
              disabled={actionLoading || !notes.trim()}
              aria-label={actionLoading ? 'Saving...' : 'Confirm skipping activity'}
              aria-disabled={!notes.trim()}
            >
              {actionLoading ? 'Saving...' : 'Skip'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
