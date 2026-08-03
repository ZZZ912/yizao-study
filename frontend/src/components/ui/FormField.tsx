import { InputHTMLAttributes, ReactNode } from "react";

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  hint?: ReactNode;
};

export function FormField({ label, error, hint, id, ...inputProps }: FormFieldProps) {
  const inputId = id ?? inputProps.name;
  const helpId = inputId ? `${inputId}-help` : undefined;

  return (
    <label className="form-field" htmlFor={inputId}>
      <span className="form-field__label">{label}</span>
      <input
        {...inputProps}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? helpId : undefined}
      />
      {error ? (
        <span className="form-field__error" id={helpId} role="alert">
          {error}
        </span>
      ) : hint ? (
        <span className="form-field__hint" id={helpId}>
          {hint}
        </span>
      ) : null}
    </label>
  );
}
