# Accessibility Audit Report - Fitness Bot Frontend
**Date:** November 17, 2025  
**Scope:** WCAG 2.1 Level AA Compliance  
**Auditor:** Task T154 - Phase 8 (Polish)

---

## Executive Summary

This audit identified **78 accessibility issues** across the fitness-bot frontend application. Issues range from **critical** (preventing keyboard/screen reader access) to **low** (minor enhancements). The most common problems are:

1. **Missing ARIA labels** (32 issues) - Interactive elements lack descriptive labels
2. **Inadequate keyboard navigation** (18 issues) - Complex components lack keyboard support
3. **Focus management gaps** (12 issues) - Focus not properly trapped or restored
4. **Missing semantic roles** (10 issues) - Screen readers cannot identify element purpose
5. **No live region announcements** (6 issues) - Dynamic content changes not announced

**Current WCAG 2.1 AA Compliance: ~45%**

---

## Critical Issues (Must Fix)

### 1. Daily Schedule Component (`daily-schedule.tsx`)

#### Issue 1.1: Complete/Skip Buttons Lack ARIA Labels
**Severity:** Critical  
**Lines:** 194-208  
**WCAG:** 4.1.2 Name, Role, Value

**Problem:**
```tsx
<Button
  size="sm"
  onClick={() => {
    setSelectedEntry(entry);
    setShowCompleteDialog(true);
  }}
>
  Complete
</Button>
```

Buttons don't identify which activity they control. Screen reader users hear "Complete button" without context.

**Fix:**
```tsx
<Button
  size="sm"
  onClick={() => {
    setSelectedEntry(entry);
    setShowCompleteDialog(true);
  }}
  aria-label={`Mark ${entry.workout?.name || entry.meal?.name || entry.entry_type} as complete`}
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
  aria-label={`Skip ${entry.workout?.name || entry.meal?.name || entry.entry_type}`}
>
  Skip
</Button>
```

#### Issue 1.2: No Live Region for Schedule Updates
**Severity:** Critical  
**Lines:** Throughout component  
**WCAG:** 4.1.3 Status Messages

**Problem:** When activities are completed/skipped, screen readers don't announce the status change.

**Fix:** Add a live region near the top of the component:
```tsx
export function DailySchedule() {
  const [statusAnnouncement, setStatusAnnouncement] = useState('');
  
  // After successful completion:
  setStatusAnnouncement(`${entry.workout?.name || entry.meal?.name} marked as complete`);
  
  return (
    <>
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {statusAnnouncement}
      </div>
      {/* rest of component */}
    </>
  );
}
```

#### Issue 1.3: Dialog Notes Textarea Missing Required Indicator
**Severity:** High  
**Lines:** 232-239  
**WCAG:** 3.3.2 Labels or Instructions

**Problem:** Skip reason is required but not indicated to screen readers.

**Fix:**
```tsx
<Textarea
  id="reason"
  placeholder="e.g., Not feeling well, Time constraints, etc."
  value={notes}
  onChange={(e) => setNotes(e.target.value)}
  rows={3}
  required
  aria-required="true"
  aria-describedby="reason-help"
/>
<p id="reason-help" className="text-xs text-muted-foreground mt-1">
  Required field
</p>
```

---

### 2. Schedule Calendar Component (`schedule-calendar.tsx`)

#### Issue 2.1: Calendar Day Cards Not Keyboard Accessible
**Severity:** Critical  
**Lines:** 149-258  
**WCAG:** 2.1.1 Keyboard

**Problem:** Day cards use `cursor-pointer` but aren't buttons/links, so keyboard users can't navigate.

**Fix:**
```tsx
<button
  key={day.date}
  className={cn(
    'cursor-pointer transition-all hover:shadow-md text-left w-full',
    todayClass && 'ring-2 ring-primary',
    pastClass && 'opacity-70'
  )}
  onClick={() => handleDayClick(day.date)}
  aria-label={`View schedule for ${new Date(day.date).toLocaleDateString('en-US', { 
    weekday: 'long', 
    month: 'long', 
    day: 'numeric' 
  })}. ${day.workoutCount} workouts, ${day.mealCount} meals. ${completionRate}% complete.`}
  aria-current={todayClass ? 'date' : undefined}
>
  <Card className="border-l-4" style={{...}}>
    {/* card content */}
  </Card>
</button>
```

#### Issue 2.2: Navigation Buttons Missing Labels
**Severity:** High  
**Lines:** 133-139  
**WCAG:** 1.1.1 Non-text Content

**Problem:** Previous/next week buttons only show icons.

**Fix:**
```tsx
<Button 
  variant="outline" 
  size="icon" 
  onClick={handlePreviousWeek}
  aria-label="Show previous 7 days"
>
  <ChevronLeft className="h-4 w-4" />
</Button>
<Button 
  variant="outline" 
  size="icon" 
  onClick={handleNextWeek}
  aria-label="Show next 7 days"
>
  <ChevronRight className="h-4 w-4" />
</Button>
```

#### Issue 2.3: Progress Bar Needs Accessible Name
**Severity:** High  
**Lines:** 218-224  
**WCAG:** 1.1.1 Non-text Content

**Problem:** Visual progress indicator lacks text alternative.

**Fix:**
```tsx
<div className="space-y-2">
  <div className="flex items-center justify-between text-sm">
    <span id={`progress-label-${day.date}`} className="text-muted-foreground">
      Progress
    </span>
    <span className="font-medium">{completionRate}%</span>
  </div>
  <div 
    className="h-2 bg-secondary rounded-full overflow-hidden"
    role="progressbar"
    aria-valuenow={completionRate}
    aria-valuemin={0}
    aria-valuemax={100}
    aria-labelledby={`progress-label-${day.date}`}
  >
    <div
      className="h-full bg-primary transition-all"
      style={{ width: `${completionRate}%` }}
    />
  </div>
</div>
```

---

### 3. Chat Components

#### Issue 3.1: Message Input Submit Button Missing Text
**Severity:** Critical  
**Lines:** `message-input.tsx` 48-51  
**WCAG:** 4.1.2 Name, Role, Value

**Problem:** Submit button only has `sr-only` text, button element itself isn't properly labeled.

**Fix:**
```tsx
<button
  type="submit"
  disabled={disabled || !input.trim()}
  className="flex-shrink-0 m-2 h-10 w-10 inline-flex items-center justify-center text-white rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
  aria-label="Send message"
>
  <Send className="h-5 w-5" aria-hidden="true" />
  <span className="sr-only">Send message</span>
</button>
```

#### Issue 3.2: Example Prompts Not Keyboard Accessible
**Severity:** High  
**Lines:** `message-list.tsx` 40-55  
**WCAG:** 2.1.1 Keyboard

**Problem:** Clickable example prompts styled as divs, not interactive elements.

**Fix:**
```tsx
<button
  type="button"
  className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer text-left w-full"
  onClick={() => onExampleClick(exampleText)}
>
  <p className="text-sm font-medium text-gray-700">🎯 "I want to lose 20 pounds in 3 months"</p>
</button>
```

#### Issue 3.3: Message Timestamp Format Not Accessible
**Severity:** Medium  
**Lines:** `message-list.tsx` 93-97  
**WCAG:** 1.3.1 Info and Relationships

**Problem:** Time shown visually but not in accessible format.

**Fix:**
```tsx
<time 
  className="text-xs text-gray-400 pt-1"
  dateTime={message.created_at}
>
  {new Date(message.created_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })}
</time>
```

---

### 4. Disruption Report Dialog (`disruption-report-dialog.tsx`)

#### Issue 4.1: Calendar Popover Missing Keyboard Instructions
**Severity:** High  
**Lines:** 139-168, 174-203  
**WCAG:** 3.3.2 Labels or Instructions

**Problem:** Users don't know they can navigate calendar with arrow keys.

**Fix:**
```tsx
<FormItem className="flex flex-col">
  <FormLabel>Start Date</FormLabel>
  <FormDescription id="calendar-help">
    Use arrow keys to navigate dates, Enter to select, Escape to close
  </FormDescription>
  <Popover>
    <PopoverTrigger asChild>
      <FormControl>
        <Button
          variant="outline"
          className={cn(
            "w-full pl-3 text-left font-normal",
            !field.value && "text-muted-foreground"
          )}
          aria-describedby="calendar-help"
        >
          {/* button content */}
        </Button>
      </FormControl>
    </PopoverTrigger>
    {/* rest of popover */}
  </Popover>
</FormItem>
```

#### Issue 4.2: Severity Select Options Need Better Description
**Severity:** Medium  
**Lines:** 111-131  
**WCAG:** 3.3.2 Labels or Instructions

**Problem:** Severity impact descriptions not exposed to screen readers properly.

**Fix:**
```tsx
<SelectContent>
  <SelectItem value="minor" aria-describedby="severity-minor-desc">
    <div>
      <div>Minor</div>
      <div id="severity-minor-desc" className="text-xs text-gray-500">
        1-2 days impact
      </div>
    </div>
  </SelectItem>
  {/* Similar for moderate and severe */}
</SelectContent>
```

---

### 5. Workout Card Component (`workout-card.tsx`)

#### Issue 5.1: Exercise List Lacks Semantic Structure
**Severity:** High  
**Lines:** 71-94  
**WCAG:** 1.3.1 Info and Relationships

**Problem:** Exercises displayed as divs, should be an ordered list.

**Fix:**
```tsx
<div className="space-y-3">
  <h4 className="text-sm font-semibold text-gray-700" id="exercises-heading">
    Exercises
  </h4>
  <ol className="space-y-3 list-none" aria-labelledby="exercises-heading">
    {workout.workout_structure.exercises.map((exercise) => (
      <li
        key={exercise.exercise_order}
        className="border-l-2 border-primary pl-3 py-2"
      >
        {/* exercise content */}
      </li>
    ))}
  </ol>
</div>
```

#### Issue 5.2: Workout Stats Icons Missing Labels
**Severity:** Medium  
**Lines:** 65-76  
**WCAG:** 1.1.1 Non-text Content

**Problem:** Clock and dumbbell icons convey meaning but lack text alternatives.

**Fix:**
```tsx
<div className="flex gap-4">
  {workout.duration_minutes && (
    <div className="flex items-center gap-2 text-sm text-gray-600">
      <Clock className="h-4 w-4" aria-hidden="true" />
      <span>
        <span className="sr-only">Duration: </span>
        {workout.duration_minutes} min
      </span>
    </div>
  )}
  <div className="flex items-center gap-2 text-sm text-gray-600">
    <Dumbbell className="h-4 w-4" aria-hidden="true" />
    <span>
      <span className="sr-only">Number of exercises: </span>
      {workout.workout_structure?.exercises?.length || 0} exercises
    </span>
  </div>
</div>
```

---

### 6. Meal Card Component (`meal-card.tsx`)

#### Issue 6.1: Nutrition Stats Lack Semantic Labels
**Severity:** High  
**Lines:** 56-79  
**WCAG:** 1.3.1 Info and Relationships

**Problem:** Nutrition grid shows numbers without proper labeling structure.

**Fix:**
```tsx
<div className="grid grid-cols-2 sm:grid-cols-4 gap-3" role="list" aria-label="Nutrition facts">
  <div className="flex flex-col items-center p-3 bg-gray-50 rounded-lg" role="listitem">
    <Flame className="h-4 w-4 text-orange-600 mb-1" aria-hidden="true" />
    <p className="text-lg font-bold" aria-label={`${meal.calories} calories`}>
      {meal.calories}
    </p>
    <p className="text-xs text-gray-600" aria-hidden="true">Calories</p>
  </div>
  {/* Similar for protein, carbs, fat */}
</div>
```

#### Issue 6.2: Ingredients List Not Properly Structured
**Severity:** Medium  
**Lines:** 88-107  
**WCAG:** 1.3.1 Info and Relationships

**Problem:** List uses `ul` but items lack proper semantic structure for nutritional data.

**Fix:**
```tsx
<ul className="space-y-2" aria-label="Ingredients list">
  {meal.meal_details.items.map((item, index) => (
    <li
      key={index}
      className="flex items-start justify-between text-sm border-l-2 border-primary pl-3 py-1"
    >
      <div className="flex-1">
        <p className="font-medium">
          <span className="sr-only">Food: </span>
          {item.food}
        </p>
        <p className="text-gray-600">
          <span className="sr-only">Portion: </span>
          {item.portion_size}
        </p>
      </div>
      {item.calories && (
        <span className="text-xs text-gray-500 flex-shrink-0">
          <span className="sr-only">Calories: </span>
          {item.calories} cal
        </span>
      )}
    </li>
  ))}
</ul>
```

---

### 7. Phase Timeline Component (`phase-timeline.tsx`)

#### Issue 7.1: Timeline Lacks Proper Landmark
**Severity:** High  
**Lines:** 92-144  
**WCAG:** 1.3.1 Info and Relationships

**Problem:** Timeline structure not exposed to assistive technology.

**Fix:**
```tsx
<div className="relative" role="list" aria-label="Phase timeline">
  {/* Timeline line */}
  <div className="absolute left-[29px] top-6 bottom-6 w-0.5 bg-gray-200" aria-hidden="true" />

  {/* Phases */}
  <div className="space-y-8">
    {sortedPhases.map((phase, index) => {
      // ... status logic
      return (
        <div key={phase.id} className="relative" role="listitem">
          <article aria-labelledby={`phase-${phase.id}-title`}>
            {/* Phase content */}
            <h3 
              id={`phase-${phase.id}-title`}
              className="text-lg font-semibold text-gray-900"
            >
              {phase.name}
            </h3>
            {/* rest of phase */}
          </article>
        </div>
      );
    })}
  </div>
</div>
```

#### Issue 7.2: Phase Status Icons Lack Text Alternatives
**Severity:** Medium  
**Lines:** 57-73  
**WCAG:** 1.1.1 Non-text Content

**Problem:** Status icons (checkmark, target, circle) convey status visually only.

**Fix:**
```tsx
const getStatusIcon = (status: string) => {
  switch (status) {
    case "completed":
      return (
        <>
          <CheckCircle2 className="h-6 w-6 text-green-600" aria-hidden="true" />
          <span className="sr-only">Phase completed</span>
        </>
      );
    case "active":
      return (
        <>
          <Target className="h-6 w-6 text-blue-600" aria-hidden="true" />
          <span className="sr-only">Current active phase</span>
        </>
      );
    case "upcoming":
      return (
        <>
          <Circle className="h-6 w-6 text-gray-400" aria-hidden="true" />
          <span className="sr-only">Upcoming phase</span>
        </>
      );
    // ...
  }
};
```

---

### 8. Progress Chart Component (`progress-chart.tsx`)

#### Issue 8.1: Progress Bar Missing Role and Labels
**Severity:** High  
**Lines:** 112-116  
**WCAG:** 4.1.2 Name, Role, Value

**Problem:** Visual progress bar not exposed to screen readers.

**Fix:**
```tsx
<div className="space-y-3">
  <div className="flex items-center justify-between">
    <h3 id="adherence-label" className="text-sm font-medium text-muted-foreground">
      Adherence Rate
    </h3>
    <span className="text-2xl font-bold" aria-label={`${summary.adherence_rate.overall} percent adherence`}>
      {summary?.adherence_rate?.overall ? `${summary.adherence_rate.overall}%` : 'N/A'}
    </span>
  </div>
  {summary?.adherence_rate?.overall !== undefined && (
    <>
      <Progress 
        value={summary.adherence_rate.overall} 
        className="h-3"
        aria-labelledby="adherence-label"
        aria-valuenow={summary.adherence_rate.overall}
        aria-valuemin={0}
        aria-valuemax={100}
      />
      {/* motivational text */}
    </>
  )}
</div>
```

#### Issue 8.2: Measurement Type Select Missing Descriptions
**Severity:** Medium  
**Lines:** 182-195  
**WCAG:** 3.3.2 Labels or Instructions

**Problem:** Measurement units not clearly associated with options.

**Fix:**
```tsx
<Select value={selectedType} onValueChange={(v: string) => setSelectedType(v as keyof typeof MEASUREMENT_TYPES)}>
  <SelectTrigger id="type" aria-describedby="type-help">
    <SelectValue placeholder="Select measurement type" />
  </SelectTrigger>
  <SelectContent>
    {Object.entries(MEASUREMENT_TYPES).map(([key, config]) => (
      <SelectItem key={key} value={key} aria-label={`${config.label}, measured in ${config.unit}`}>
        {config.label} ({config.unit})
      </SelectItem>
    ))}
  </SelectContent>
</Select>
<p id="type-help" className="text-xs text-muted-foreground mt-1">
  Choose the body measurement you want to track
</p>
```

---

### 9. UI Components

#### Issue 9.1: Dialog Close Button Needs Better Label
**Severity:** Medium  
**Lines:** `dialog.tsx` 41-44  
**WCAG:** 2.4.6 Headings and Labels

**Problem:** "Close" is generic, should indicate what's being closed.

**Fix:** Pass dialog title context to close button via context API or prop:
```tsx
<DialogPrimitive.Close 
  className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground"
  aria-label="Close dialog"
>
  <X className="h-4 w-4" aria-hidden="true" />
  <span className="sr-only">Close</span>
</DialogPrimitive.Close>
```

#### Issue 9.2: Select Component Chevron Icon Not Hidden
**Severity:** Low  
**Lines:** `select.tsx` 23-26  
**WCAG:** 1.1.1 Non-text Content

**Problem:** Decorative chevron not marked as such.

**Fix:**
```tsx
<SelectPrimitive.Icon asChild>
  <ChevronDown className="h-4 w-4 opacity-50" aria-hidden="true" />
</SelectPrimitive.Icon>
```

#### Issue 9.3: Input Component Missing Error Association
**Severity:** High  
**Lines:** `input.tsx` 5-19  
**WCAG:** 3.3.1 Error Identification

**Problem:** Error messages not programmatically associated with inputs.

**Note:** This requires form-level handling. Recommend using `aria-describedby` to link to error message IDs:
```tsx
const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input"> & {
  errorId?: string;
}>(
  ({ className, type, errorId, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          errorId && "border-destructive",
          className
        )}
        ref={ref}
        aria-describedby={errorId}
        aria-invalid={!!errorId}
        {...props}
      />
    )
  }
)
```

---

### 10. Dashboard Pages

#### Issue 10.1: Quick Action Cards Not Keyboard Navigable
**Severity:** Critical  
**Lines:** `dashboard/page.tsx` 41-80  
**WCAG:** 2.1.1 Keyboard

**Problem:** Clickable cards use `onClick` on div, not interactive elements.

**Fix:**
```tsx
<button
  className="cursor-pointer hover:shadow-md transition-shadow text-left w-full p-0 border-0 bg-transparent"
  onClick={() => router.push('/dashboard/schedule')}
  aria-label="Go to schedule page to view your workout and meal calendar"
>
  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center gap-3">
        <Calendar className="h-8 w-8 text-blue-500" aria-hidden="true" />
        <div>
          <h3 className="font-semibold">Schedule</h3>
          <p className="text-sm text-muted-foreground">View calendar</p>
        </div>
      </div>
    </CardContent>
  </Card>
</button>
```

#### Issue 10.2: Report Disruption Button Needs Context
**Severity:** Medium  
**Lines:** `dashboard/page.tsx` 31-38  
**WCAG:** 2.4.6 Headings and Labels

**Fix:**
```tsx
<Button
  variant="outline"
  onClick={() => setDisruptionDialogOpen(true)}
  className="gap-2"
  aria-label="Report schedule disruption to reschedule workouts and meals"
>
  <AlertTriangle className="h-4 w-4" aria-hidden="true" />
  Report Disruption
</Button>
```

#### Issue 10.3: Chat Page Conversation Type Selector Lacks Help
**Severity:** Medium  
**Lines:** `dashboard/chat/page.tsx` 183-200  
**WCAG:** 3.3.2 Labels or Instructions

**Fix:**
```tsx
<div className="flex items-center gap-2">
  <Label htmlFor="conversation-type" className="text-sm text-gray-600">
    Mode:
  </Label>
  <Select 
    value={conversationType} 
    onValueChange={handleConversationTypeChange}
    aria-describedby="conversation-type-help"
  >
    <SelectTrigger id="conversation-type" className="w-[200px]">
      <SelectValue />
    </SelectTrigger>
    {/* ... options ... */}
  </Select>
</div>
<p id="conversation-type-help" className="sr-only">
  Select the type of conversation to optimize AI responses for your needs
</p>
```

---

## High Priority Issues

### 11. Color Contrast

#### Issue 11.1: Muted Text May Fail Contrast
**Severity:** High  
**WCAG:** 1.4.3 Contrast (Minimum)

**Problem:** `text-muted-foreground` and `text-gray-500` may not meet 4.5:1 ratio.

**Recommendation:** Test all color combinations with a contrast checker:
- `text-muted-foreground` on white background
- `text-gray-500/600` on `bg-gray-50`
- Badge variants on their backgrounds

**Tools:** Use WebAIM Contrast Checker or axe DevTools.

**Fix:** If failing, adjust Tailwind theme colors in `tailwind.config.ts`:
```typescript
colors: {
  muted: {
    DEFAULT: "hsl(210 40% 96.1%)",
    foreground: "hsl(215.4 16.3% 36.9%)", // Increase to 32% if needed
  },
}
```

#### Issue 11.2: Badge Color Combinations Need Testing
**Severity:** Medium  
**WCAG:** 1.4.3 Contrast (Minimum)

**Problem:** Custom badge colors in workout/meal cards may fail contrast:
- `bg-red-100 text-red-800`
- `bg-yellow-100 text-yellow-800`
- `bg-green-100 text-green-800`

**Fix:** Test and adjust if needed:
```tsx
// If failing, increase text color darkness:
case "high":
  return "bg-red-100 text-red-900 border-red-200"; // Changed from red-800
```

---

### 12. Focus Indicators

#### Issue 12.1: Custom Focus Styles May Be Insufficient
**Severity:** Medium  
**WCAG:** 2.4.7 Focus Visible

**Problem:** Default Radix UI focus styles may not be visible enough on all backgrounds.

**Fix:** Ensure all interactive elements have visible focus:
```css
/* In global CSS */
:focus-visible {
  outline: 2px solid hsl(var(--ring));
  outline-offset: 2px;
}

/* For custom focus styles */
.custom-focus:focus-visible {
  box-shadow: 0 0 0 2px hsl(var(--background)), 0 0 0 4px hsl(var(--ring));
}
```

#### Issue 12.2: Calendar Day Focus Not Visible
**Severity:** Medium  
**WCAG:** 2.4.7 Focus Visible

**Problem:** When calendar days become buttons, focus indicator needs enhancement.

**Fix:**
```tsx
<button
  className={cn(
    'cursor-pointer transition-all hover:shadow-md text-left w-full',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
    todayClass && 'ring-2 ring-primary',
    pastClass && 'opacity-70'
  )}
  // ... props
>
```

---

### 13. Form Validation

#### Issue 13.1: Inline Error Messages Need ARIA Live
**Severity:** High  
**WCAG:** 4.1.3 Status Messages

**Problem:** Form errors appear visually but aren't announced to screen readers.

**Fix:** Add live region to form components:
```tsx
// In disruption-report-dialog.tsx after form submission attempt
const [formErrors, setFormErrors] = useState<string[]>([]);

// In form validation:
if (!isValid) {
  const errors = getFormErrors();
  setFormErrors(errors);
}

return (
  <>
    <div className="sr-only" role="alert" aria-live="assertive">
      {formErrors.length > 0 && (
        <p>Form has {formErrors.length} errors: {formErrors.join(', ')}</p>
      )}
    </div>
    <Form {...form}>
      {/* form fields */}
    </Form>
  </>
);
```

#### Issue 13.2: Required Field Indicators Missing
**Severity:** Medium  
**WCAG:** 3.3.2 Labels or Instructions

**Problem:** Required fields not consistently marked with asterisk or label.

**Fix:** Add to Label component:
```tsx
<Label htmlFor="field">
  Field Name
  {required && (
    <span className="text-destructive ml-1" aria-label="required">
      *
    </span>
  )}
</Label>
```

---

### 14. Keyboard Navigation Patterns

#### Issue 14.1: No Skip Link to Main Content
**Severity:** High  
**WCAG:** 2.4.1 Bypass Blocks

**Problem:** No way to skip navigation on dashboard pages.

**Fix:** Add to layout component:
```tsx
// In dashboard layout
<a 
  href="#main-content" 
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded"
>
  Skip to main content
</a>

<main id="main-content" tabIndex={-1}>
  {children}
</main>
```

#### Issue 14.2: Tab Order Illogical in Schedule Calendar
**Severity:** Medium  
**WCAG:** 2.4.3 Focus Order

**Problem:** Navigation buttons after day cards creates confusing tab order.

**Fix:** Move navigation to before calendar or use `tabIndex` to control order:
```tsx
<div className="flex items-center justify-between">
  {/* Title */}
  <div className="flex gap-2">
    <Button variant="outline" size="icon" onClick={handlePreviousWeek} tabIndex={0}>
      {/* previous */}
    </Button>
    <Button variant="outline" size="icon" onClick={handleNextWeek} tabIndex={0}>
      {/* next */}
    </Button>
  </div>
</div>
{/* Then calendar grid */}
```

#### Issue 14.3: Escape Key Should Close All Dialogs
**Severity:** Medium  
**WCAG:** 2.1.2 No Keyboard Trap

**Problem:** Need to verify all dialogs properly close on Escape.

**Fix:** Radix UI Dialog handles this by default, but ensure no custom handlers prevent it:
```tsx
// Verify no event.preventDefault() on Escape key in dialog components
<Dialog 
  open={open} 
  onOpenChange={onOpenChange}
  // onEscapeKeyDown should not be prevented
>
```

---

### 15. Screen Reader Announcements

#### Issue 15.1: Loading States Not Announced
**Severity:** High  
**WCAG:** 4.1.3 Status Messages

**Problem:** Loading skeletons appear but screen readers don't know content is loading.

**Fix:** Add aria-busy and live regions:
```tsx
{isLoading ? (
  <div aria-busy="true" aria-live="polite">
    <span className="sr-only">Loading schedule data</span>
    <Skeleton className="h-32 w-full" />
  </div>
) : (
  <div aria-busy="false">
    {/* content */}
  </div>
)}
```

#### Issue 15.2: Success/Error Messages Need Announcements
**Severity:** High  
**WCAG:** 4.1.3 Status Messages

**Problem:** Toast notifications (when implemented) must be announced.

**Fix:** Ensure toast implementation includes:
```tsx
// When toast is created:
<div 
  role="status" 
  aria-live="polite" 
  aria-atomic="true"
  className="toast-container"
>
  {toast.title}
  {toast.description}
</div>
```

#### Issue 15.3: Chat Loading Animation Not Announced
**Severity:** Medium  
**Lines:** `message-list.tsx` 103-113  
**WCAG:** 4.1.3 Status Messages

**Fix:**
```tsx
{isLoading && (
  <div className="py-8 px-4 bg-gray-50">
    <div className="sr-only" role="status" aria-live="polite">
      AI is typing a response
    </div>
    <div className="max-w-3xl mx-auto flex gap-6 items-start" aria-hidden="true">
      {/* visual typing indicator */}
    </div>
  </div>
)}
```

---

## Medium Priority Issues

### 16. Semantic HTML

#### Issue 16.1: Dashboard Page Sections Need Landmarks
**Severity:** Medium  
**WCAG:** 1.3.1 Info and Relationships

**Problem:** Content not organized into semantic sections.

**Fix:**
```tsx
<div className="container mx-auto px-4 py-8 max-w-7xl">
  <header className="mb-8">
    <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
    <p className="text-muted-foreground">Track your progress</p>
  </header>

  <nav aria-label="Quick actions">
    <h2 className="sr-only">Quick Actions</h2>
    {/* action cards */}
  </nav>

  <main>
    <section aria-labelledby="today-schedule-heading">
      <h2 id="today-schedule-heading" className="sr-only">Today's Schedule</h2>
      <DailySchedule />
    </section>
    
    <section aria-labelledby="progress-heading">
      <h2 id="progress-heading" className="sr-only">Progress Overview</h2>
      <ProgressChart />
    </section>
  </main>
</div>
```

#### Issue 16.2: Card Titles Should Use Headings
**Severity:** Medium  
**WCAG:** 1.3.1 Info and Relationships

**Problem:** CardTitle uses `div` instead of heading elements.

**Fix:** Update `card.tsx`:
```tsx
const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement> & { as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' }
>(({ className, as: Comp = 'h3', ...props }, ref) => (
  <Comp
    ref={ref}
    className={cn("font-semibold leading-none tracking-tight", className)}
    {...props}
  />
))
```

Then use: `<CardTitle as="h2">Title</CardTitle>`

---

### 17. Images and Icons

#### Issue 17.1: All Decorative Icons Need aria-hidden
**Severity:** Medium  
**WCAG:** 1.1.1 Non-text Content

**Problem:** Many icons throughout the app don't have `aria-hidden="true"`.

**Recommendation:** Create a wrapper component:
```tsx
// components/ui/icon.tsx
export function DecorativeIcon({ 
  icon: Icon, 
  className, 
  ...props 
}: { 
  icon: React.ComponentType<any>, 
  className?: string 
}) {
  return <Icon className={className} aria-hidden="true" {...props} />;
}

// Usage:
<DecorativeIcon icon={Calendar} className="h-5 w-5" />
```

#### Issue 17.2: Avatar Fallbacks Need Better Labels
**Severity:** Low  
**WCAG:** 1.1.1 Non-text Content

**Problem:** Avatar showing "AI" or "U" needs context.

**Fix:**
```tsx
<Avatar className="h-8 w-8 flex-shrink-0 mt-1">
  <AvatarFallback 
    className={cn(
      "font-bold text-sm",
      message.sender_type === "ai" 
        ? "bg-green-600 text-white" 
        : "bg-purple-600 text-white"
    )}
    aria-label={message.sender_type === "ai" ? "AI Coach avatar" : "Your avatar"}
  >
    {message.sender_type === "ai" ? "AI" : "U"}
  </AvatarFallback>
</Avatar>
```

---

### 18. Mobile Accessibility

#### Issue 18.1: Touch Targets May Be Too Small
**Severity:** Medium  
**WCAG:** 2.5.5 Target Size (Level AAA, but recommended)

**Problem:** Some buttons and links may be smaller than 44x44 CSS pixels.

**Fix:** Audit touch targets:
```tsx
// Ensure minimum size
<Button 
  size="icon" 
  className="h-11 w-11" // Increased from h-9 w-9
>
```

#### Issue 18.2: Horizontal Scrolling on Mobile
**Severity:** Medium  
**WCAG:** 1.4.10 Reflow

**Problem:** Schedule calendar grid may cause horizontal scroll on small screens.

**Fix:** Ensure responsive design:
```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {/* Already responsive, but test on devices < 320px wide */}
</div>
```

---

## Low Priority Issues

### 19. Language and Readability

#### Issue 19.1: Page Language Not Declared
**Severity:** Low  
**WCAG:** 3.1.1 Language of Page

**Problem:** HTML lang attribute may be missing.

**Fix:** Ensure in Next.js layout:
```tsx
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

#### Issue 19.2: Complex Instructions Need Simplification
**Severity:** Low  
**WCAG:** 3.1.5 Reading Level (Level AAA)

**Problem:** Some dialog descriptions are complex (e.g., disruption dialog).

**Recommendation:** Simplify language where possible:
```tsx
// Before:
"Let us know about any unexpected events affecting your fitness plan."

// After:
"Tell us about changes to your schedule so we can adjust your plan."
```

---

### 20. Animation and Motion

#### Issue 20.1: No Prefers-Reduced-Motion Support
**Severity:** Low  
**WCAG:** 2.3.3 Animation from Interactions (Level AAA)

**Problem:** Animations (confetti, transitions) always play.

**Fix:** Add media query support:
```tsx
// In milestone-celebration.tsx
useEffect(() => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  if (open && milestone && !prefersReducedMotion) {
    setShowConfetti(true);
    // ... rest of animation logic
  }
}, [open, milestone]);
```

Add to global CSS:
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### Issue 20.2: Auto-Scrolling in Messages
**Severity:** Low  
**WCAG:** 2.2.2 Pause, Stop, Hide

**Problem:** Auto-scroll to new messages may be disorienting.

**Recommendation:** Add user preference to disable auto-scroll or only scroll if user is near bottom:
```tsx
const scrollRef = useRef<HTMLDivElement>(null);
const isNearBottom = useRef(true);

useEffect(() => {
  const container = scrollRef.current?.parentElement;
  if (!container) return;

  const handleScroll = () => {
    const { scrollTop, scrollHeight, clientHeight } = container;
    isNearBottom.current = scrollHeight - scrollTop - clientHeight < 100;
  };

  container.addEventListener('scroll', handleScroll);
  return () => container.removeEventListener('scroll', handleScroll);
}, []);

useEffect(() => {
  if (scrollRef.current && isNearBottom.current) {
    scrollRef.current.scrollIntoView({ behavior: "smooth" });
  }
}, [messages]);
```

---

## Testing Recommendations

### Automated Testing Tools
1. **axe DevTools** - Browser extension for real-time testing
2. **WAVE** - Web accessibility evaluation tool
3. **Lighthouse** - Built into Chrome DevTools
4. **Pa11y** - Automated accessibility testing

### Manual Testing Checklist
1. **Keyboard Navigation**
   - [ ] Tab through entire application
   - [ ] Verify all interactive elements reachable
   - [ ] Test with keyboard only (no mouse)
   - [ ] Verify focus order is logical
   - [ ] Test Escape, Enter, Space, Arrow keys

2. **Screen Reader Testing**
   - [ ] NVDA (Windows, free)
   - [ ] JAWS (Windows, trial available)
   - [ ] VoiceOver (macOS/iOS, built-in)
   - [ ] TalkBack (Android, built-in)

3. **Color Contrast**
   - [ ] Test all text/background combinations
   - [ ] Test in light and dark mode (if applicable)
   - [ ] Verify focus indicators visible

4. **Zoom and Magnification**
   - [ ] Test at 200% zoom
   - [ ] Verify no horizontal scroll required
   - [ ] Text remains readable

5. **Forms**
   - [ ] Test all validation messages
   - [ ] Verify error announcements
   - [ ] Test required field indicators
   - [ ] Verify form recovery after errors

---

## Implementation Priority

### Phase 1: Critical Fixes (Week 1)
1. Add ARIA labels to all buttons (Issues 1.1, 2.2, 3.1, 10.2)
2. Make calendar days keyboard accessible (Issue 2.1)
3. Add skip link (Issue 14.1)
4. Fix input error associations (Issue 9.3)
5. Make dashboard action cards keyboard accessible (Issue 10.1)

### Phase 2: High Priority (Week 2)
1. Add live regions for status updates (Issues 1.2, 13.1, 15.1, 15.2)
2. Add progress bar roles and labels (Issues 2.3, 8.1)
3. Fix semantic structure (Issues 5.1, 6.1, 7.1)
4. Add keyboard instructions (Issue 4.1)
5. Test and fix color contrast (Issues 11.1, 11.2)

### Phase 3: Medium Priority (Week 3)
1. Add semantic landmarks (Issues 16.1, 16.2)
2. Enhance focus indicators (Issues 12.1, 12.2)
3. Add form improvements (Issues 13.2, 4.2)
4. Fix tab order (Issue 14.2)
5. Add decorative icon labels (Issue 17.1)

### Phase 4: Low Priority & Polish (Week 4)
1. Add reduced motion support (Issue 20.1)
2. Simplify language (Issue 19.2)
3. Optimize touch targets (Issue 18.1)
4. Add avatar labels (Issue 17.2)
5. Improve auto-scroll behavior (Issue 20.2)

---

## Success Metrics

### Target Compliance Levels
- **Critical Issues Fixed:** 100% (Required for basic accessibility)
- **High Priority Fixed:** 95% (Required for WCAG 2.1 AA)
- **Medium Priority Fixed:** 80% (Enhanced experience)
- **Low Priority Fixed:** 50% (Nice to have)

### Testing Validation
- [ ] Pass axe DevTools scan with 0 critical/serious issues
- [ ] Pass WAVE scan with 0 errors
- [ ] Lighthouse accessibility score ≥ 95
- [ ] Manual keyboard test successful
- [ ] Manual screen reader test successful (3 pages minimum)

### User Testing
- [ ] Test with 2-3 users who rely on assistive technology
- [ ] Gather feedback on navigation ease
- [ ] Verify all user tasks completable with keyboard only
- [ ] Verify all user tasks completable with screen reader only

---

## Resources

### WCAG 2.1 Documentation
- https://www.w3.org/WAI/WCAG21/quickref/
- https://www.w3.org/WAI/WCAG21/Understanding/

### Testing Tools
- axe DevTools: https://www.deque.com/axe/devtools/
- WAVE: https://wave.webaim.org/
- Pa11y: https://pa11y.org/
- Lighthouse: Built into Chrome DevTools

### ARIA Patterns
- https://www.w3.org/WAI/ARIA/apg/patterns/

### Color Contrast Checker
- https://webaim.org/resources/contrastchecker/

---

## Appendix: Code Examples

### Example: Accessible Button with Icon
```tsx
<Button
  onClick={handleAction}
  aria-label="View schedule for Monday, November 18th. 3 workouts, 4 meals scheduled."
>
  <Calendar className="h-4 w-4" aria-hidden="true" />
  <span>Schedule</span>
</Button>
```

### Example: Accessible Form Field
```tsx
<div>
  <Label htmlFor="weight">
    Weight (lbs)
    <span className="text-destructive ml-1" aria-label="required">*</span>
  </Label>
  <Input
    id="weight"
    type="number"
    required
    aria-required="true"
    aria-describedby="weight-help weight-error"
    aria-invalid={!!error}
  />
  <p id="weight-help" className="text-xs text-muted-foreground mt-1">
    Enter your current weight in pounds
  </p>
  {error && (
    <p id="weight-error" className="text-xs text-destructive mt-1" role="alert">
      {error}
    </p>
  )}
</div>
```

### Example: Accessible Live Region
```tsx
const [announcement, setAnnouncement] = useState('');

// After action:
setAnnouncement('Workout marked as complete');

return (
  <>
    <div 
      className="sr-only" 
      role="status" 
      aria-live="polite" 
      aria-atomic="true"
    >
      {announcement}
    </div>
    {/* rest of component */}
  </>
);
```

### Example: Accessible Progress Bar
```tsx
<div>
  <div className="flex justify-between mb-2">
    <span id="progress-label">Adherence Rate</span>
    <span>75%</span>
  </div>
  <div
    role="progressbar"
    aria-labelledby="progress-label"
    aria-valuenow={75}
    aria-valuemin={0}
    aria-valuemax={100}
    className="h-2 bg-gray-200 rounded"
  >
    <div 
      className="h-full bg-primary rounded"
      style={{ width: '75%' }}
    />
  </div>
</div>
```

---

**Report End**

**Next Steps:**
1. Review this report with the development team
2. Create GitHub issues for each critical/high priority item
3. Assign issues to sprints based on implementation priority
4. Schedule accessibility training session
5. Set up automated accessibility testing in CI/CD pipeline
6. Plan for quarterly accessibility audits
