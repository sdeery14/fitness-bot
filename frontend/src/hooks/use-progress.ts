/**
 * useProgress Hook - Fetch and manage progress data
 * 
 * Provides:
 * - Progress summary (adherence rates, streaks)
 * - Measurement logging (weight, body fat %, etc.)
 * - Measurement history
 */

import { useCallback, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ProgressSummary {
  adherence_rate: {
    overall: number;
    workouts: number;
    meals: number;
  };
  current_streak: {
    days: number;
    start_date: string;
  };
  recent_measurements: Array<{
    record_date: string;
    weight_lbs: number | null;
    body_fat_percentage: number | null;
    energy_level: number | null;
    mood: string | null;
  }>;
}

export interface Measurement {
  id: string;
  record_date: string;
  record_type: string;
  weight_lbs: number | null;
  body_fat_percentage: number | null;
  measurements: Record<string, number> | null;
  energy_level: number | null;
  mood: string | null;
  user_notes: string | null;
}

export interface MeasurementInput {
  record_type: 'weight' | 'measurement';
  value?: number;
  unit?: string;
  weight_lbs?: number;
  body_fat_percentage?: number;
  measurements?: Record<string, number>;
  energy_level?: number;
  mood?: string;
  user_notes?: string;
  recorded_at?: string;
}

export function useProgress() {
  const [summary, setSummary] = useState<ProgressSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [measurementsLoading, setMeasurementsLoading] = useState(false);
  const [measurementsError, setMeasurementsError] = useState<string | null>(null);

  /**
   * Fetch progress summary
   * @param fitnessP lanId - Optional fitness plan ID to filter by
   */
  const fetchSummary = useCallback(async (fitnessPlanId?: string) => {
    setSummaryLoading(true);
    setSummaryError(null);

    try {
      const url = fitnessPlanId
        ? `${API_BASE}/progress?fitness_plan_id=${fitnessPlanId}`
        : `${API_BASE}/progress`;

      const token = localStorage.getItem('access_token');
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch progress summary: ${response.statusText}`);
      }

      const data: ProgressSummary = await response.json();
      setSummary(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setSummaryError(message);
      console.error('Error fetching progress summary:', error);
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  /**
   * Fetch measurement history
   * @param recordType - Optional filter by record type
   * @param limit - Number of measurements to fetch
   */
  const fetchMeasurements = useCallback(
    async (recordType?: string, limit: number = 10) => {
      setMeasurementsLoading(true);
      setMeasurementsError(null);

      try {
        const params = new URLSearchParams();
        if (recordType) params.append('type', recordType);
        params.append('limit', limit.toString());

        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/progress/measurements?${params}`, {
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch measurements: ${response.statusText}`);
        }

        const data: Measurement[] = await response.json();
        setMeasurements(data);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        setMeasurementsError(message);
        console.error('Error fetching measurements:', error);
      } finally {
        setMeasurementsLoading(false);
      }
    },
    []
  );

  /**
   * Log a new measurement
   * @param measurement - Measurement data
   */
  const logMeasurement = useCallback(async (measurement: MeasurementInput) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/progress/measurements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(measurement),
      });

      if (!response.ok) {
        throw new Error(`Failed to log measurement: ${response.statusText}`);
      }

      const data: Measurement = await response.json();
      
      // Refresh measurements list
      await fetchMeasurements();
      
      // Refresh summary to get updated stats
      await fetchSummary();
      
      return data;
    } catch (error) {
      console.error('Error logging measurement:', error);
      throw error;
    }
  }, [fetchMeasurements, fetchSummary]);

  return {
    // Progress summary
    summary,
    summaryLoading,
    summaryError,
    fetchSummary,

    // Measurements
    measurements,
    measurementsLoading,
    measurementsError,
    fetchMeasurements,
    logMeasurement,
  };
}
