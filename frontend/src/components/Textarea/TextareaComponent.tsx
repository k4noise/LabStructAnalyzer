import { UseFormRegisterReturn } from "react-hook-form";

interface TextareaProps {
  className: string;
  placeholder: string;
  readonly?: boolean;
  value?: string;
  minRowsCount?: number;
  max?: number;
  validationOptions?: UseFormRegisterReturn;
}

const Textarea = ({
  className,
  placeholder,
  readonly = false,
  value,
  minRowsCount,
  max,
  validationOptions,
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
    ></textarea>
  );
};

export default Textarea;
