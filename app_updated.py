# Updated login route only
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        login_type = data.get('loginType', 'email')
        login_value = data.get('loginValue') or data.get('email')
        password = data.get('password')

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        if login_type == 'mobile':
            cursor.execute('''
                SELECT Name, Roll_Number, Class, Email, Mobile, Username, Photo FROM Student_details
                WHERE Mobile = ? AND Password = ?
            ''', (login_value, password))
        else:
            cursor.execute('''
                SELECT Name, Roll_Number, Class, Email, Mobile, Username, Photo FROM Student_details
                WHERE Email = ? AND Password = ?
            ''', (login_value, password))
            
        result = cursor.fetchone()
        conn.close()

        if result:
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['otp_user'] = login_value

            name, roll_number, class_name, email, mobile, username, photo_path = result

            # Send OTP based on login type
            if login_type == 'mobile':
                try:
                    send_sms_otp(mobile, otp, name)
                    return jsonify({'success': True, 'message': f'OTP sent to {mobile}. Please verify OTP to complete login.'})
                except Exception:
                    return jsonify({'success': False, 'message': 'Failed to send SMS. Please try email login.'})
            else:
                msg = Message(
                    subject="Your OTP Code",
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )
                msg.body = f"Hello {name},\n\nYour OTP is: {otp}\nThis code is valid for 5 minutes."
                mail.send(msg)
                return jsonify({'success': True, 'message': f'OTP sent to {email}. Please verify OTP to complete login.'})
        else:
            field_name = 'mobile number' if login_type == 'mobile' else 'email'
            return jsonify({'success': False, 'message': f'Invalid {field_name} or password.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})