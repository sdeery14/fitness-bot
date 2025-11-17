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

  useEffect(() => {
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
          <CardDescription>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</CardDescription>
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
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Today&apos;s Schedule</CardTitle>
              <CardDescription>
                {new Date(todaySchedule.date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{completionRate}%</div>
              <div className="text-sm text-muted-foreground">Completed</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4 pb-4 border-b">
              <div>
                <div className="text-sm text-muted-foreground">Workouts</div>
                <div className="text-lg font-semibold">
                  {summary.completed_workouts} / {summary.total_workouts}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Meals</div>
                <div className="text-lg font-semibold">
                  {summary.completed_meals} / {summary.total_meals}
                </div>
              </div>
            </div>

            {/* Schedule Entries */}
            <div className="space-y-3">
              {entries.map((entry) => (
                <Card key={entry.id} className="border-l-4" style={{
                  borderLeftColor: entry.entry_type === 'workout' ? '#3b82f6' : '#f97316'
                }}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        {getIcon(entry.entry_type)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold">
                              {entry.workout?.name || entry.meal?.name || `${entry.entry_type}`}
                            </h4>
                            {getStatusBadge(entry.completion_status)}
                          </div>
                          {entry.entry_time && (
                            <p className="text-sm text-muted-foreground mt-1">
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
                              Note: {entry.user_notes}
                            </p>
                          )}
                        </div>
                      </div>
                      {entry.completion_status === 'scheduled' && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedEntry(entry);
                              setShowCompleteDialog(true);
                            }}
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
                          >
                            Skip
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Complete Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Mark as Complete</DialogTitle>
            <DialogDescription>
              Add any notes about this {selectedEntry?.entry_type} (optional)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                placeholder="How did it go? Any observations?"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompleteDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleComplete} disabled={actionLoading}>
              {actionLoading ? 'Saving...' : 'Complete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Skip Dialog */}
      <Dialog open={showSkipDialog} onOpenChange={setShowSkipDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Skip Activity</DialogTitle>
            <DialogDescription>
              Please provide a reason for skipping this {selectedEntry?.entry_type}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="reason">Reason</Label>
              <Textarea
                id="reason"
                placeholder="e.g., Not feeling well, Time constraints, etc."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSkipDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSkip} disabled={actionLoading || !notes.trim()}>
              {actionLoading ? 'Saving...' : 'Skip'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
