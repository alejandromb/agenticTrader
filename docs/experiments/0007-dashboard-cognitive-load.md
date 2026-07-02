# Experiment 0007: Dashboard cognitive load

- Status: Accepted
- Baseline: Milestone 7 unified dashboard

## Hypothesis

Question-led progressive disclosure can preserve every workflow while reducing
the number of simultaneous top-level choices and dense forms.

## Baseline

- Four equal-priority workspace choices were visible in the main navigation.
- Four Quant forms were visible simultaneously.
- Two Monitoring forms were visible simultaneously.
- The human disposition checkpoint appeared after all memo sections.
- Reviews emphasized creation and saved packets equally.

## Target

- Two primary workspace choices: Research and Reviews.
- Quant and Monitoring remain one action away under Tools.
- Zero advanced forms are expanded by default.
- Each advanced disclosure states the investment question it answers.
- Thesis and known limitations precede the human checkpoint.
- The human checkpoint precedes full memo and model metadata.
- No existing form, API, or domain capability is removed.

## Acceptance evidence

- structural tests for navigation hierarchy and form containment;
- complete HTTP workflow regression suite;
- JavaScript syntax validation;
- desktop and mobile browser inspection; and
- zero new analytics or execution paths.

## Result

- Primary navigation choices decreased from four to two: Research and Reviews.
- Quant and Monitoring remain reachable through one Tools disclosure.
- Seven advanced forms remain present but zero are expanded by default; at most
  one form can be open in each advanced workspace.
- All seven disclosures state the question or decision task they support.
- The human checkpoint now follows the thesis and known limitations directly;
  full memo sections and model metadata are available in one secondary disclosure.
- The full regression suite passed with 120 tests, and JavaScript syntax checks
  passed.
- Real-database browser inspection verified Research, Tools, Quant, and a TXN
  decision record. At 390px viewport width, document width remained 390px with
  zero horizontal overflow and zero advanced forms expanded.
- Browser console inspection reported zero errors.
- No analytics, model, API, automation, or execution capability was added or
  removed.

## Conclusion

Accepted. The dashboard preserves the complete operator workspace while giving
research review and human decisions a materially clearer hierarchy.
