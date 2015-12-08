from django.conf import settings

demo_username = settings.DEMO_USERNAME
demo_user_password = settings.DEMO_PASSWORD

minimal_password_length = 8
birthdate_placeholder = '1980-02-16'
sex_placeholder = 'male'
handedness_placeholder = 'right'
language_placeholder = 'english'
firstname_placeholder = 'Your first name'
username_placeholder = 'Your email address'
forgot_your_password_title = 'Forgot your password?'

demographic_variables = [
    ('Date_of_Birth', True),
    ('Handedness', True),
    ('Sex', True),
    ('Native_Language', True)
]

demographic_variables_placeholders = dict([
    ('Date_of_Birth', birthdate_placeholder),
    ('Handedness', handedness_placeholder),
    ('Sex', sex_placeholder),
    ('Native_Language', language_placeholder)
])

reset_password_email = '''
This is a message from {5}. Your new password is: {1}

To login again, go to 

{2}

regards,
{4}.'''

