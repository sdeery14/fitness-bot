'use client';

import { useState, useCallback } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

interface WorkoutDetail {
  id: string;
  name: string;
  workout_type: string;
  duration_minutes: number;
  difficulty_level: string;
  workout_details: {
    exercises?: Array<{
      name: string;
      sets?: number;
      reps?: string;
      duration?: number;
      rest_seconds?: number;
      notes?: string;
      equipment?: string;
    }>;
    warmup?: string;
    cooldown?: string;
    notes?: string;
  };
}

export function useWorkoutDetail() {
  const [workout, setWorkout] = useState<WorkoutDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkout = useCallback(async (workoutId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/workouts/${workoutId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch workout details');
      }

      const data = await response.json();
      setWorkout(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  return { workout, loading, error, fetchWorkout };
}
