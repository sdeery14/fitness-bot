/**
 * Progress Chart Component - Visualize adherence rates, streaks, and measurements
 * 
 * Features:
 * - Adherence rate display with visual indicator
 * - Streak tracking (current and best)
 * - Recent measurements (weight, body fat %, etc.)
 * - Add new measurements
 * - Responsive design
 */

'use client';

import { useEffect, useState } from 'react';
import { useProgress } from '@/hooks/use-progress';
import type { MeasurementInput } from '@/hooks/use-progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Flame, Plus, Activity, Weight, Ruler } from 'lucide-react';

interface ProgressChartProps {
  fitnessPlanId?: string;
}

const MEASUREMENT_TYPES = {
  weight: { label: 'Weight', unit: 'lbs', icon: Weight },
  body_fat_percentage: { label: 'Body Fat %', unit: '%', icon: Activity },
  chest: { label: 'Chest', unit: 'in', icon: Ruler },
  waist: { label: 'Waist', unit: 'in', icon: Ruler },
  hips: { label: 'Hips', unit: 'in', icon: Ruler },
  biceps: { label: 'Biceps', unit: 'in', icon: Ruler },
  thighs: { label: 'Thighs', unit: 'in', icon: Ruler },
} as const;

export function ProgressChart({ fitnessPlanId }: ProgressChartProps) {
  const { summary, measurements, summaryLoading, measurementsLoading, fetchSummary, fetchMeasurements, logMeasurement } =
    useProgress();

  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedType, setSelectedType] = useState<keyof typeof MEASUREMENT_TYPES>('weight');
  const [value, setValue] = useState('');
  const [notes, setNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchSummary(fitnessPlanId);
    fetchMeasurements(undefined, 10);
  }, [fitnessPlanId, fetchSummary, fetchMeasurements]);

  const handleAddMeasurement = async () => {
    if (!value || !selectedType) return;

    setActionLoading(true);
    try {
      const data: MeasurementInput = {
        record_type: selectedType === 'weight' || selectedType === 'body_fat_percentage' ? 'weight' : 'measurement',
        weight_lbs: selectedType === 'weight' ? parseFloat(value) : undefined,
        body_fat_percentage: selectedType === 'body_fat_percentage' ? parseFloat(value) : undefined,
        measurements: selectedType !== 'weight' && selectedType !== 'body_fat_percentage' 
          ? { [selectedType]: parseFloat(value) }
          : undefined,
        user_notes: notes || undefined,
      };
      await logMeasurement(data);
      setShowAddDialog(false);
      setValue('');
      setNotes('');
    } catch (error) {
      console.error('Failed to log measurement:', error);
    } finally {
      setActionLoading(false);
    }
  };



  if (summaryLoading && measurementsLoading) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {/* Adherence & Streak Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Progress Overview</CardTitle>
              <Button size="sm" onClick={() => setShowAddDialog(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Measurement
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Adherence Rate */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-muted-foreground">Adherence Rate</h3>
                  <span className="text-2xl font-bold">
                    {summary?.adherence_rate?.overall ? `${summary.adherence_rate.overall}%` : 'N/A'}
                  </span>
                </div>
                {summary?.adherence_rate?.overall !== undefined && (
                  <>
                    <Progress value={summary.adherence_rate.overall} className="h-3" />
                    <p className="text-xs text-muted-foreground">
                      {(summary.adherence_rate.overall ?? 0) >= 80
                        ? 'Excellent! Keep up the great work!'
                        : (summary.adherence_rate.overall ?? 0) >= 60
                        ? 'Good progress, stay consistent!'
                        : 'Let\'s work on consistency together!'}
                    </p>
                  </>
                )}
              </div>

              {/* Streak */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-muted-foreground">Current Streak</h3>
                  <div className="flex items-center gap-2">
                    <Flame className="h-5 w-5 text-orange-500" />
                    <span className="text-2xl font-bold">{summary?.current_streak?.days || 0}</span>
                    <span className="text-sm text-muted-foreground">days</span>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {(summary?.current_streak?.days || 0) === 0
                    ? 'Start your streak today!'
                    : 'Keep it going!'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Measurements */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Measurements</CardTitle>
            <CardDescription>Track your physical progress over time</CardDescription>
          </CardHeader>
          <CardContent>
            {measurementsLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : measurements && measurements.length > 0 ? (
              <div className="space-y-3">
                {measurements.map((measurement) => {
                  // Display weight or body fat % from measurement
                  const weightValue = measurement.weight_lbs;
                  const bodyFatValue = measurement.body_fat_percentage;
                  
                  const displayType = weightValue ? 'weight' : bodyFatValue ? 'body_fat_percentage' : null;
                  if (!displayType) return null;
                  
                  const config = MEASUREMENT_TYPES[displayType];
                  const Icon = config?.icon || Activity;
                  const displayValue = displayType === 'weight' ? weightValue : bodyFatValue;

                  return (
                    <Card key={measurement.id} className="border-l-4" style={{
                      borderLeftColor: '#6b7280'
                    }}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Icon className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="font-semibold">
                                  {config?.label}
                                </h4>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {new Date(measurement.record_date).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric',
                                })}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold">
                              {displayValue}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {config?.unit || ''}
                            </div>
                          </div>
                        </div>
                        {measurement.user_notes && (
                          <p className="text-sm text-muted-foreground mt-2 italic">
                            {measurement.user_notes}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <p className="text-muted-foreground mb-4">No measurements recorded yet</p>
                <Button onClick={() => setShowAddDialog(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Your First Measurement
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Add Measurement Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Measurement</DialogTitle>
            <DialogDescription>
              Record a new body measurement to track your progress
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="type">Measurement Type</Label>
              <Select value={selectedType} onValueChange={(v: string) => setSelectedType(v as keyof typeof MEASUREMENT_TYPES)}>
                <SelectTrigger id="type">
                  <SelectValue placeholder="Select measurement type" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MEASUREMENT_TYPES).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="value">
                Value ({MEASUREMENT_TYPES[selectedType]?.unit})
              </Label>
              <Input
                id="value"
                type="number"
                step="0.1"
                placeholder="Enter value"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="notes">Notes (Optional)</Label>
              <Input
                id="notes"
                placeholder="Any observations or context?"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddMeasurement} disabled={actionLoading || !value}>
              {actionLoading ? 'Saving...' : 'Add Measurement'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
