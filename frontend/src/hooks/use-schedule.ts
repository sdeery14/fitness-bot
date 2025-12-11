/**
 * useSchedule Hook - Fetch and manage schedule data
 * 
 * Provides:
 * - Today's schedule fetching
 * - Upcoming schedule fetching (14-day view)
 * - Mark entry as complete
 * - Skip entry with reason
 * - Automatic revalidation
 */

import { useCallback } from 'react';
import { useScheduleStore } from '@/store/schedule-store';
import type { TodaySchedule, UpcomingSchedule, ScheduleEntry } from '@/store/schedule-store';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export function useSchedule() {
  const {
    todaySchedule,
    todayLoading,
    todayError,
    upcomingSchedule,
    upcomingLoading,
    upcomingError,
    setTodaySchedule,
    setTodayLoading,
    setTodayError,
    setUpcomingSchedule,
    setUpcomingLoading,
    setUpcomingError,
    updateEntryStatus,
    confirmUpdate,
    rollbackUpdate,
  } = useScheduleStore();

  /**
   * Fetch today's schedule
   */
  const fetchTodaySchedule = useCallback(async () => {
    setTodayLoading(true);
    setTodayError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/schedules/today`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch today's schedule: ${response.statusText}`);
      }

      const data: TodaySchedule = await response.json();
      setTodaySchedule(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setTodayError(message);
      console.error('Error fetching today schedule:', error);
    } finally {
      setTodayLoading(false);
    }
  }, [setTodaySchedule, setTodayLoading, setTodayError]);

  /**
   * Fetch upcoming schedule
   * @param days - Number of days to fetch (default: 14)
   */
  const fetchUpcomingSchedule = useCallback(
    async (days: number = 14) => {
      setUpcomingLoading(true);
      setUpcomingError(null);

      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/schedules/upcoming?days=${days}`, {
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch upcoming schedule: ${response.statusText}`);
        }

        const data: UpcomingSchedule = await response.json();
        setUpcomingSchedule(data);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        setUpcomingError(message);
        console.error('Error fetching upcoming schedule:', error);
      } finally {
        setUpcomingLoading(false);
      }
    },
    [setUpcomingSchedule, setUpcomingLoading, setUpcomingError]
  );

  /**
   * Mark entry as complete
   * @param entryId - Schedule entry ID
   * @param notes - Optional user notes
   */
  const markComplete = useCallback(
    async (entryId: string, notes?: string) => {
      // Optimistic update
      updateEntryStatus(entryId, 'completed', notes);

      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/schedules/entries/${entryId}/complete`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({ user_notes: notes }),
        });

        if (!response.ok) {
          // Rollback optimistic update on error
          rollbackUpdate(entryId);
          throw new Error(`Failed to mark entry as complete: ${response.statusText}`);
        }

        const updatedEntry: ScheduleEntry = await response.json();
        
        // Confirm the optimistic update
        confirmUpdate(entryId);
        
        // Refresh today's schedule to get updated summary
        await fetchTodaySchedule();
        
        return updatedEntry;
      } catch (error) {
        console.error('Error marking entry as complete:', error);
        throw error;
      }
    },
    [updateEntryStatus, confirmUpdate, rollbackUpdate, fetchTodaySchedule]
  );

  /**
   * Skip entry with reason
   * @param entryId - Schedule entry ID
   * @param reason - Reason for skipping
   */
  const skipEntry = useCallback(
    async (entryId: string, reason: string) => {
      // Optimistic update
      updateEntryStatus(entryId, 'skipped', reason);

      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/schedules/entries/${entryId}/skip`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({ reason }),
        });

        if (!response.ok) {
          // Rollback optimistic update on error
          rollbackUpdate(entryId);
          throw new Error(`Failed to skip entry: ${response.statusText}`);
        }

        const updatedEntry: ScheduleEntry = await response.json();
        
        // Confirm the optimistic update
        confirmUpdate(entryId);
        
        // Refresh today's schedule
        await fetchTodaySchedule();
        
        return updatedEntry;
      } catch (error) {
        console.error('Error skipping entry:', error);
        throw error;
      }
    },
    [updateEntryStatus, confirmUpdate, rollbackUpdate, fetchTodaySchedule]
  );

  return {
    // Today's schedule
    todaySchedule,
    todayLoading,
    todayError,
    fetchTodaySchedule,

    // Upcoming schedule
    upcomingSchedule,
    upcomingLoading,
    upcomingError,
    fetchUpcomingSchedule,

    // Actions
    markComplete,
    skipEntry,
  };
}
