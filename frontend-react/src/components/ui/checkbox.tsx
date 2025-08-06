import * as React from "react"
import { Check } from "lucide-react"
import { cn } from "../../lib/utils"

interface CheckboxProps {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
  disabled?: boolean
  className?: string
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ checked, onCheckedChange, disabled, className, ...props }, ref) => {
    return (
      <div className="relative inline-flex items-center">
        <input
          ref={ref}
          type="checkbox"
          checked={checked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          disabled={disabled}
          className="sr-only"
          {...props}
        />
        <div
          className={cn(
            "h-4 w-4 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            checked ? "bg-primary text-primary-foreground" : "bg-background",
            className
          )}
          onClick={() => !disabled && onCheckedChange?.(!checked)}
        >
          {checked && (
            <Check className="h-3 w-3 text-white" />
          )}
        </div>
      </div>
    )
  }
)
Checkbox.displayName = "Checkbox"

export { Checkbox }
