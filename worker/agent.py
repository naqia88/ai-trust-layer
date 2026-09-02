# Import the shared function that creates actions in the required schema.
from action_schema import create_action


# Create a money-transfer action for trust evaluation.
def create_transfer_money_action(amount, currency, recipient, description):
    return create_action(
        action_type="transfer_money",
        details={
            "amount": amount,
            "currency": currency,
            "recipient": recipient,
            "description": description,
        },
    )


# Create an email action for trust evaluation.
def create_send_email_action(to, subject, body, has_attachment, attachment_name):
    return create_action(
        action_type="send_email",
        details={
            "to": to,
            "subject": subject,
            "body": body,
            "has_attachment": has_attachment,
            "attachment_name": attachment_name,
        },
    )


# Create a code-execution action for trust evaluation.
def create_execute_code_action(code, environment, language):
    return create_action(
        action_type="execute_code",
        details={
            "code": code,
            "environment": environment,
            "language": language,
        },
    )


# Send an action to the trust interceptor before it can be executed.
def submit_action(action):
    from trust.interceptor import intercept_action

    return intercept_action(action)
