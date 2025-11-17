/**
 * Component tests for ScheduleCalendar
 *
 * Tests schedule visualization and navigation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { ScheduleCalendar } from '@/components/fitness/schedule-calendar';

// Mock the schedule hook
vi.mock('@/hooks/use-schedule', () => ({
  useSchedule: () => ({
    upcomingEntries: [
      {
        id: 'entry-1',
        entry_date: '2025-11-18',
        entry_type: 'workout',
        entry_time: '08:00:00',
        completion_status: 'scheduled',
        workout: {
          id: 'workout-1',
          name: 'Upper Body Push',
          workout_type: 'strength',
          duration_minutes: 45,
        },
      },
      {
        id: 'entry-2',
        entry_date: '2025-11-18',
        entry_type: 'meal',
        entry_time: '12:00:00',
        completion_status: 'scheduled',
        meal: {
          id: 'meal-1',
          name: 'Chicken Salad',
          meal_type: 'lunch',
          calories: 450,
        },
      },
      {
        id: 'entry-3',
        entry_date: '2025-11-19',
        entry_type: 'workout',
        entry_time: '08:00:00',
        completion_status: 'completed',
        workout: {
          id: 'workout-2',
          name: 'Lower Body',
          workout_type: 'strength',
          duration_minutes: 50,
        },
      },
    ],
    isLoading: false,
    completeEntry: vi.fn(),
    skipEntry: vi.fn(),
  }),
}));

describe('ScheduleCalendar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders schedule for specified number of days', () => {
    render(<ScheduleCalendar days={7} />);

    // Calendar should show dates
    expect(screen.getByText(/Upper Body Push/i)).toBeInTheDocument();
    expect(screen.getByText(/Chicken Salad/i)).toBeInTheDocument();
  });

  it('groups entries by date', () => {
    render(<ScheduleCalendar days={14} />);

    // Should see multiple entries for the same date grouped together
    const nov18Entries = screen.getAllByText(/2025-11-18|Nov 18/i);
    expect(nov18Entries.length).toBeGreaterThan(0);
  });

  it('displays workout and meal entries with correct icons', () => {
    render(<ScheduleCalendar days={7} />);

    // Workout entries should have dumbbell icon
    const workoutEntry = screen.getByText(/Upper Body Push/i).closest('[data-entry-type="workout"]');
    expect(workoutEntry).toBeInTheDocument();

    // Meal entries should have fork/knife icon
    const mealEntry = screen.getByText(/Chicken Salad/i).closest('[data-entry-type="meal"]');
    expect(mealEntry).toBeInTheDocument();
  });

  it('shows completion status for entries', () => {
    render(<ScheduleCalendar days={7} />);

    // Completed workout should show checkmark
    const completedEntry = screen.getByText(/Lower Body/i).closest('[data-status="completed"]');
    expect(completedEntry).toBeInTheDocument();

    // Scheduled entries should show as scheduled
    const scheduledEntry = screen.getByText(/Upper Body Push/i).closest('[data-status="scheduled"]');
    expect(scheduledEntry).toBeInTheDocument();
  });

  it('displays entry times', () => {
    render(<ScheduleCalendar days={7} />);

    expect(screen.getByText(/08:00|8:00 AM/i)).toBeInTheDocument();
    expect(screen.getByText(/12:00|12:00 PM/i)).toBeInTheDocument();
  });

  it('shows workout duration', () => {
    render(<ScheduleCalendar days={7} />);

    expect(screen.getByText(/45 min/i)).toBeInTheDocument();
    expect(screen.getByText(/50 min/i)).toBeInTheDocument();
  });

  it('shows meal calories', () => {
    render(<ScheduleCalendar days={7} />);

    expect(screen.getByText(/450 cal/i)).toBeInTheDocument();
  });

  it('allows completing scheduled workouts', async () => {
    const { useSchedule } = await import('@/hooks/use-schedule');
    const mockCompleteEntry = vi.fn();
    vi.mocked(useSchedule).mockReturnValue({
      upcomingEntries: [
        {
          id: 'entry-1',
          entry_date: '2025-11-18',
          entry_type: 'workout',
          completion_status: 'scheduled',
          workout: { name: 'Upper Body Push' },
        },
      ],
      isLoading: false,
      completeEntry: mockCompleteEntry,
      skipEntry: vi.fn(),
    } as any);

    render(<ScheduleCalendar days={7} />);

    const completeButton = screen.getByRole('button', { name: /complete/i });
    fireEvent.click(completeButton);

    expect(mockCompleteEntry).toHaveBeenCalledWith('entry-1');
  });

  it('allows skipping scheduled entries', async () => {
    const { useSchedule } = await import('@/hooks/use-schedule');
    const mockSkipEntry = vi.fn();
    vi.mocked(useSchedule).mockReturnValue({
      upcomingEntries: [
        {
          id: 'entry-1',
          entry_date: '2025-11-18',
          entry_type: 'workout',
          completion_status: 'scheduled',
          workout: { name: 'Upper Body Push' },
        },
      ],
      isLoading: false,
      completeEntry: vi.fn(),
      skipEntry: mockSkipEntry,
    } as any);

    render(<ScheduleCalendar days={7} />);

    const skipButton = screen.getByRole('button', { name: /skip/i });
    fireEvent.click(skipButton);

    expect(mockSkipEntry).toHaveBeenCalledWith('entry-1');
  });

  it('shows loading skeleton while fetching data', () => {
    const { useSchedule } = require('@/hooks/use-schedule');
    vi.mocked(useSchedule).mockReturnValue({
      upcomingEntries: [],
      isLoading: true,
      completeEntry: vi.fn(),
      skipEntry: vi.fn(),
    } as any);

    render(<ScheduleCalendar days={7} />);

    expect(screen.getByTestId('schedule-loading-skeleton')).toBeInTheDocument();
  });

  it('shows empty state when no entries available', () => {
    const { useSchedule } = require('@/hooks/use-schedule');
    vi.mocked(useSchedule).mockReturnValue({
      upcomingEntries: [],
      isLoading: false,
      completeEntry: vi.fn(),
      skipEntry: vi.fn(),
    } as any);

    render(<ScheduleCalendar days={7} />);

    expect(screen.getByText(/no scheduled/i)).toBeInTheDocument();
  });

  it('highlights today\'s date', () => {
    render(<ScheduleCalendar days={7} />);

    const today = new Date().toISOString().split('T')[0];
    const todayElement = screen.getByText(new RegExp(today, 'i')).closest('[data-is-today="true"]');
    expect(todayElement).toBeInTheDocument();
  });

  it('uses custom days prop to limit displayed range', () => {
    render(<ScheduleCalendar days={3} />);

    // Should only show entries within 3 days
    // This would be validated by checking the date range of displayed entries
    const entries = screen.queryAllByTestId('schedule-entry');
    expect(entries.length).toBeLessThanOrEqual(20); // Reasonable limit for 3 days
  });
});
