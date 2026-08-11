import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function fuzzyDateValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const val = control.value;
    if (!val || typeof val !== 'string' || !val.trim()) {
      return null;
    }
    const cleaned = val.trim();
    const pattern = /^\d{4}(?:[/.-](?:0?[1-9]|1[0-2]|xx)(?:[/.-](?:0?[1-9]|[12]\d|3[01]|xx))?)?$/i;
    if (!pattern.test(cleaned)) {
      return { invalidFuzzyDate: true };
    }
    return null;
  };
}
