interface ButtonProps {
  text: string;
  type?: "button" | "submit" | "reset";
  name?: string;
  classes?: string;
  onClick?: () => void;
  disable?: boolean;
}

const Button = ({
  text,
  type = "button",
  name,
  classes,
  onClick,
  disable,
}: ButtonProps) => (
  <button
    className={`px-2 py-1 border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950
      transition-colors duration-300
      dark:hover:bg-zinc-200/20 hover:bg-zinc-500/30  focus:outline-none focus:border-blue-500 dark:focus:text-blue-300 focus:text-blue-600 ${
        classes ? `${classes}` : ""
      }`}
    type={type}
    name={name}
    onClick={onClick}
    disabled={disable}
  >
    {text}
  </button>
);

export default Button;
