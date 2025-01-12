import { UseFormRegisterReturn } from "react-hook-form";

interface TextareaProps {
  className: string;
  placeholder: string;
  readonly?: boolean;
  value?: string;
  minRowsCount?: number;
  max?: number;
  validationOptions?: UseFormRegisterReturn;
  disabled?: boolean;
  onChange?;
}

const Textarea = ({
  className,
  placeholder,
  readonly = false,
  value,
  minRowsCount,
  max,
  validationOptions,
  disabled,
  onChange,
}: TextareaProps) => {
  const resize = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = event.currentTarget;
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
  };

  return (
    <textarea
      {...validationOptions}
      rows={minRowsCount}
      className={className}
      placeholder={placeholder}
      onInput={resize}
      readOnly={readonly}
      maxLength={max}
      defaultValue={value}
      onChange={onChange}
      disabled={disabled}
    ></textarea>
  );
};

export default Textarea;
