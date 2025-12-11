'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useWorkoutDetail } from '@/hooks/use-workout-detail';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Dumbbell, Clock, TrendingUp } from 'lucide-react';

export default function WorkoutDetailPage() {
  const params = useParams();
  const router = useRouter();
  const workoutId = params.id as string;
  const { workout, loading, error, fetchWorkout } = useWorkoutDetail();

  useEffect(() => {
    if (workoutId) {
      fetchWorkout(workoutId);
    }
  }, [workoutId, fetchWorkout]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !workout) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8">
            <p className="text-destructive">Error loading workout: {error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const exercises = workout.workout_details?.exercises || [];

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{workout.name}</h1>
          <p className="text-muted-foreground capitalize">{workout.workout_type} workout</p>
        </div>
      </div>

      {/* Workout Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Duration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{workout.duration_minutes} min</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Difficulty
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge className="text-lg capitalize">{workout.difficulty_level}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Dumbbell className="h-5 w-5" />
              Exercises
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{exercises.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Warmup */}
      {workout.workout_details?.warmup && (
        <Card>
          <CardHeader>
            <CardTitle>Warm-up</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{workout.workout_details.warmup}</p>
          </CardContent>
        </Card>
      )}

      {/* Exercises */}
      <Card>
        <CardHeader>
          <CardTitle>Exercises</CardTitle>
          <CardDescription>{exercises.length} exercise{exercises.length !== 1 ? 's' : ''} in this workout</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {exercises.map((exercise, index) => (
            <div key={index}>
              {index > 0 && <Separator className="my-6" />}
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">{exercise.name}</h3>
                    {exercise.equipment && (
                      <p className="text-sm text-muted-foreground capitalize">Equipment: {exercise.equipment}</p>
                    )}
                  </div>
                  <Badge variant="outline">Exercise {index + 1}</Badge>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {exercise.sets && (
                    <div>
                      <p className="text-sm text-muted-foreground">Sets</p>
                      <p className="text-lg font-semibold">{exercise.sets}</p>
                    </div>
                  )}
                  {exercise.reps && (
                    <div>
                      <p className="text-sm text-muted-foreground">Reps</p>
                      <p className="text-lg font-semibold">{exercise.reps}</p>
                    </div>
                  )}
                  {exercise.duration && (
                    <div>
                      <p className="text-sm text-muted-foreground">Duration</p>
                      <p className="text-lg font-semibold">{exercise.duration}s</p>
                    </div>
                  )}
                  {exercise.rest_seconds && (
                    <div>
                      <p className="text-sm text-muted-foreground">Rest</p>
                      <p className="text-lg font-semibold">{exercise.rest_seconds}s</p>
                    </div>
                  )}
                </div>

                {exercise.notes && (
                  <p className="text-sm text-muted-foreground italic">{exercise.notes}</p>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Cooldown */}
      {workout.workout_details?.cooldown && (
        <Card>
          <CardHeader>
            <CardTitle>Cool-down</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{workout.workout_details.cooldown}</p>
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      {workout.workout_details?.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{workout.workout_details.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
