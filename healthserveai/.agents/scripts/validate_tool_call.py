import sys
import json
import re

def main():
    try:
        # Read from stdin
        input_data = sys.stdin.read()
        if not input_data:
            # If stdin is empty, default to allow
            print(json.dumps({"decision": "allow", "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}))
            sys.exit(0)

        data = json.loads(input_data)
        tool_call = data.get("toolCall", {})
        args = tool_call.get("args", {})

        # Check command line
        command_line = args.get("CommandLine") or args.get("command_line") or args.get("command") or ""

        # Destructive patterns
        destructive_patterns = [
            r"rm\s+-rf\s+/",
            r"rm\s+-rf\s+\*",
            r"rm\s+-f\s+/",
            r"rm\s+-r\s+/",
            r"format\s+[a-zA-Z]:",
            r"del\s+/f\s+/q\s+/s",
        ]

        is_destructive = False
        for pattern in destructive_patterns:
            if re.search(pattern, command_line):
                is_destructive = True
                break

        if is_destructive:
            reason = f"Blocked destructive command execution: '{command_line}'"
            sys.stderr.write(reason + "\n")
            print(json.dumps({
                "decision": "block",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason
                }
            }))
            sys.exit(2)
        else:
            print(json.dumps({
                "decision": "allow",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": "Allowed"
                }
            }))
            sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Error in validation script: {str(e)}\n")
        print(json.dumps({
            "decision": "block",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Validation script error: {str(e)}"
            }
        }))
        sys.exit(2)

if __name__ == "__main__":
    main()
