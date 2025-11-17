"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dumbbell, Clock, Flame } from "lucide-react";

interface Exercise {
  exercise_order: number;
  name: string;
  sets: number;
  reps: string;
  rest_seconds?: number;
  target_muscle_groups: string[];
  equipment?: string;
  instructions?: string;
}

interface Workout {
  id: string;
  name: string;
  type: string;
  duration_minutes?: number;
  intensity: string;
  workout_structure: {
    exercises: Exercise[];
  };
}

interface WorkoutCardProps {
  workout: Workout;
  phaseNumber?: number;
  weekNumber?: number;
}

export function WorkoutCard({ workout, phaseNumber, weekNumber }: WorkoutCardProps) {
  const getIntensityColor = (intensity: string) => {
    switch (intensity.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-800 border-red-200";
      case "moderate":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <Card className="w-full" role="article" aria-labelledby={`workout-${workout.id}-title`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl" id={`workout-${workout.id}-title`}>
              {workout.name}
            </CardTitle>
            <CardDescription className="mt-1">
              {phaseNumber && `Phase ${phaseNumber}`}
              {weekNumber && ` • Week ${weekNumber}`}
              {workout.type && ` • ${workout.type}`}
            </CardDescription>
          </div>
          <Badge 
            className={getIntensityColor(workout.intensity)} 
            variant="outline"
            aria-label={`Intensity: ${workout.intensity}`}
          >
            <Flame className="h-3 w-3 mr-1" aria-hidden="true" />
            {workout.intensity}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Workout Stats */}
        <div className="flex gap-4" role="list" aria-label="Workout details">
          {workout.duration_minutes && (
            <div className="flex items-center gap-2 text-sm text-gray-600" role="listitem">
              <Clock className="h-4 w-4" aria-hidden="true" />
              <span>
                <span className="sr-only">Duration: </span>
                {workout.duration_minutes} minutes
              </span>
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-gray-600" role="listitem">
            <Dumbbell className="h-4 w-4" aria-hidden="true" />
            <span>
              <span className="sr-only">Total exercises: </span>
              {workout.workout_structure?.exercises?.length || 0} exercises
            </span>
          </div>
        </div>

        {/* Exercises List */}
        {workout.workout_structure?.exercises && workout.workout_structure.exercises.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-700" id={`workout-${workout.id}-exercises`}>
              Exercises
            </h4>
            <ol className="space-y-3 list-none" aria-labelledby={`workout-${workout.id}-exercises`}>
              {workout.workout_structure.exercises.map((exercise) => (
                <li
                  key={exercise.exercise_order}
                  className="border-l-2 border-primary pl-3 py-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="font-medium text-sm">
                        {exercise.exercise_order}. {exercise.name}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        <span className="sr-only">Sets: </span>
                        {exercise.sets} sets
                        <span className="sr-only">, Reps: </span>
                        {' × '}{exercise.reps} reps
                        {exercise.rest_seconds && (
                          <>
                            <span className="sr-only">, Rest: </span>
                            {` • ${exercise.rest_seconds} seconds rest`}
                          </>
                        )}
                      </p>
                      {exercise.target_muscle_groups && exercise.target_muscle_groups.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2" role="list" aria-label="Target muscles">
                          {exercise.target_muscle_groups.map((muscle) => (
                            <Badge key={muscle} variant="secondary" className="text-xs" role="listitem">
                              {muscle}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    {exercise.equipment && (
                      <Badge variant="outline" className="text-xs flex-shrink-0" aria-label={`Equipment: ${exercise.equipment}`}>
                        {exercise.equipment}
                      </Badge>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
