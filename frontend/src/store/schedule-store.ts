/**
 * Schedule Store - Zustand state management for schedule entries and completion tracking
 * 
 * Manages:
 * - Today's schedule entries
 * - Upcoming schedule entries (14-day view)
 * - Entry completion state
 * - Loading and error states
 */

import { create } from 'zustand';

export interface ScheduleEntry {
  id: string;
  entry_type: 'workout' | 'meal';
  entry_date: string;
  entry_time: string | null;
  workout_id: string | null;
  meal_id: string | null;
  workout_name: string | null;
  meal_name: string | null;
  completion_status: 'scheduled' | 'completed' | 'skipped' | 'rescheduled';
  completed_at: string | null;
  user_notes: string | null;
  workout?: {
    id: string;
    name: string;
    description: string;
  };
  meal?: {
    id: string;
    name: string;
    description: string;
  };
}

export interface TodaySchedule {
  date: string;
  entries: ScheduleEntry[];
  summary: {
    total_workouts: number;
    total_meals: number;
    completed_workouts: number;
    completed_meals: number;
  };
}

export interface UpcomingSchedule {
  start_date: string;
  end_date: string;
  entries: ScheduleEntry[];
  grouped_by_date: Record<string, ScheduleEntry[]>;
}

interface ScheduleState {
  // Today's schedule
  todaySchedule: TodaySchedule | null;
  todayLoading: boolean;
  todayError: string | null;

  // Upcoming schedule
  upcomingSchedule: UpcomingSchedule | null;
  upcomingLoading: boolean;
  upcomingError: string | null;

  // Optimistic update tracking
  pendingUpdates: Map<string, ScheduleEntry>;

  // Actions
  setTodaySchedule: (schedule: TodaySchedule) => void;
  setTodayLoading: (loading: boolean) => void;
  setTodayError: (error: string | null) => void;

  setUpcomingSchedule: (schedule: UpcomingSchedule) => void;
  setUpcomingLoading: (loading: boolean) => void;
  setUpcomingError: (error: string | null) => void;

  // Optimistic update: immediately update UI, track for rollback
  updateEntryStatus: (entryId: string, status: ScheduleEntry['completion_status'], notes?: string) => void;
  
  // Confirm optimistic update (remove from pending after successful API call)
  confirmUpdate: (entryId: string) => void;
  
  // Rollback optimistic update (revert to previous state on API error)
  rollbackUpdate: (entryId: string) => void;

  // Clear all data
  reset: () => void;
}

const initialState = {
  todaySchedule: null,
  todayLoading: false,
  todayError: null,
  upcomingSchedule: null,
  upcomingLoading: false,
  upcomingError: null,
  pendingUpdates: new Map<string, ScheduleEntry>(),
};

export const useScheduleStore = create<ScheduleState>((set) => ({
  ...initialState,

  setTodaySchedule: (schedule) => set({ todaySchedule: schedule }),
  setTodayLoading: (loading) => set({ todayLoading: loading }),
  setTodayError: (error) => set({ todayError: error }),

  setUpcomingSchedule: (schedule) => set({ upcomingSchedule: schedule }),
  setUpcomingLoading: (loading) => set({ upcomingLoading: loading }),
  setUpcomingError: (error) => set({ upcomingError: error }),

  updateEntryStatus: (entryId, status, notes) =>
    set((state) => {
      // Store original entry for rollback
      const pendingUpdates = new Map(state.pendingUpdates);
      
      // Find the original entry
      let originalEntry: ScheduleEntry | undefined;
      if (state.todaySchedule) {
        originalEntry = state.todaySchedule.entries.find((e) => e.id === entryId);
      }
      if (!originalEntry && state.upcomingSchedule) {
        originalEntry = state.upcomingSchedule.entries.find((e) => e.id === entryId);
      }
      
      if (originalEntry && !pendingUpdates.has(entryId)) {
        pendingUpdates.set(entryId, originalEntry);
      }
      // Update in today's schedule
      if (state.todaySchedule) {
        const updatedEntries = state.todaySchedule.entries.map((entry) =>
          entry.id === entryId
            ? {
                ...entry,
                completion_status: status,
                completed_at: status === 'completed' || status === 'skipped' ? new Date().toISOString() : null,
                user_notes: notes || entry.user_notes,
              }
            : entry
        );

        // Recalculate summary
        const completedWorkouts = updatedEntries.filter(
          (e) => e.entry_type === 'workout' && e.completion_status === 'completed'
        ).length;
        const completedMeals = updatedEntries.filter(
          (e) => e.entry_type === 'meal' && e.completion_status === 'completed'
        ).length;

        return {
          pendingUpdates,
          todaySchedule: {
            ...state.todaySchedule,
            entries: updatedEntries,
            summary: {
              ...state.todaySchedule.summary,
              completed_workouts: completedWorkouts,
              completed_meals: completedMeals,
            },
          },
        };
      }

      // Update in upcoming schedule
      if (state.upcomingSchedule) {
        const updatedEntries = state.upcomingSchedule.entries.map((entry) =>
          entry.id === entryId
            ? {
                ...entry,
                completion_status: status,
                completed_at: status === 'completed' || status === 'skipped' ? new Date().toISOString() : null,
                user_notes: notes || entry.user_notes,
              }
            : entry
        );

        // Rebuild grouped_by_date
        const grouped: Record<string, ScheduleEntry[]> = {};
        updatedEntries.forEach((entry) => {
          if (!grouped[entry.entry_date]) {
            grouped[entry.entry_date] = [];
          }
          grouped[entry.entry_date].push(entry);
        });

        return {
          pendingUpdates,
          upcomingSchedule: {
            ...state.upcomingSchedule,
            entries: updatedEntries,
            grouped_by_date: grouped,
          },
        };
      }

      return { pendingUpdates };
    }),

  confirmUpdate: (entryId) =>
    set((state) => {
      const pendingUpdates = new Map(state.pendingUpdates);
      pendingUpdates.delete(entryId);
      return { pendingUpdates };
    }),

  rollbackUpdate: (entryId) =>
    set((state) => {
      const originalEntry = state.pendingUpdates.get(entryId);
      if (!originalEntry) return state;

      const pendingUpdates = new Map(state.pendingUpdates);
      pendingUpdates.delete(entryId);

      // Rollback in today's schedule
      if (state.todaySchedule) {
        const updatedEntries = state.todaySchedule.entries.map((entry) =>
          entry.id === entryId ? originalEntry : entry
        );

        // Recalculate summary
        const completedWorkouts = updatedEntries.filter(
          (e) => e.entry_type === 'workout' && e.completion_status === 'completed'
        ).length;
        const completedMeals = updatedEntries.filter(
          (e) => e.entry_type === 'meal' && e.completion_status === 'completed'
        ).length;

        return {
          pendingUpdates,
          todaySchedule: {
            ...state.todaySchedule,
            entries: updatedEntries,
            summary: {
              ...state.todaySchedule.summary,
              completed_workouts: completedWorkouts,
              completed_meals: completedMeals,
            },
          },
        };
      }

      // Rollback in upcoming schedule
      if (state.upcomingSchedule) {
        const updatedEntries = state.upcomingSchedule.entries.map((entry) =>
          entry.id === entryId ? originalEntry : entry
        );

        // Rebuild grouped_by_date
        const grouped: Record<string, ScheduleEntry[]> = {};
        updatedEntries.forEach((entry) => {
          if (!grouped[entry.entry_date]) {
            grouped[entry.entry_date] = [];
          }
          grouped[entry.entry_date].push(entry);
        });

        return {
          pendingUpdates,
          upcomingSchedule: {
            ...state.upcomingSchedule,
            entries: updatedEntries,
            grouped_by_date: grouped,
          },
        };
      }

      return { pendingUpdates };
    }),

  reset: () => set(initialState),
}));
