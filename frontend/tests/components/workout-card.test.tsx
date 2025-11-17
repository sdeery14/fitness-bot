/**
 * Component tests for WorkoutCard
 *
 * Tests workout display and completion tracking
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WorkoutCard } from '@/components/fitness/workout-card';
import type { Workout } from '@/types/fitness';

const mockWorkout: Workout = {
  id: 'workout-123',
  name: 'Upper Body Strength',
  workout_type: 'strength',
  duration_minutes: 45,
  intensity: 'moderate',
  description: 'Focus on compound upper body movements',
  exercises: [
    {
      exercise_id: 'ex-1',
      name: 'Bench Press',
      sets: 4,
      reps: '8-10',
      rest_seconds: 90,
      notes: 'Control the eccentric',
    },
    {
      exercise_id: 'ex-2',
      name: 'Bent Over Rows',
      sets: 4,
      reps: '10-12',
      rest_seconds: 90,
      notes: 'Keep back flat',
    },
  ],
};

describe('WorkoutCard', () => {
  const mockOnComplete = vi.fn();
  const mockOnSkip = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workout details correctly', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText('Upper Body Strength')).toBeInTheDocument();
    expect(screen.getByText(/45 min/i)).toBeInTheDocument();
    expect(screen.getByText(/moderate/i)).toBeInTheDocument();
  });

  it('displays all exercises in the workout', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText('Bench Press')).toBeInTheDocument();
    expect(screen.getByText('Bent Over Rows')).toBeInTheDocument();
    expect(screen.getByText('4 × 8-10')).toBeInTheDocument();
    expect(screen.getByText('4 × 10-12')).toBeInTheDocument();
  });

  it('shows exercise notes when available', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText(/Control the eccentric/i)).toBeInTheDocument();
    expect(screen.getByText(/Keep back flat/i)).toBeInTheDocument();
  });

  it('calls onComplete when mark complete button clicked', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const completeButton = screen.getByRole('button', { name: /mark complete/i });
    fireEvent.click(completeButton);

    expect(mockOnComplete).toHaveBeenCalledWith(mockWorkout.id);
  });

  it('calls onSkip when skip button clicked', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const skipButton = screen.getByRole('button', { name: /skip/i });
    fireEvent.click(skipButton);

    expect(mockOnSkip).toHaveBeenCalledWith(mockWorkout.id);
  });

  it('displays completed state when status is completed', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        status="completed"
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText(/completed/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /mark complete/i })).toBeDisabled();
  });

  it('displays skipped state when status is skipped', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        status="skipped"
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText(/skipped/i)).toBeInTheDocument();
  });

  it('shows intensity badge with correct color', () => {
    const { container } = render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={1}
        weekNumber={2}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    const badge = screen.getByText(/moderate/i);
    expect(badge).toHaveClass('bg-yellow-100'); // Moderate intensity color
  });

  it('displays phase and week information', () => {
    render(
      <WorkoutCard
        workout={mockWorkout}
        phaseNumber={2}
        weekNumber={5}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText(/Phase 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Week 5/i)).toBeInTheDocument();
  });

  it('renders without crash when exercises array is empty', () => {
    const emptyWorkout = { ...mockWorkout, exercises: [] };

    render(
      <WorkoutCard
        workout={emptyWorkout}
        phaseNumber={1}
        weekNumber={1}
        onComplete={mockOnComplete}
        onSkip={mockOnSkip}
      />
    );

    expect(screen.getByText('Upper Body Strength')).toBeInTheDocument();
  });
});
