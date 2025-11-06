// Simple Language System
const translations = {
  en: {
    'admin_login': 'Admin Login',
    'voter_login': 'Voter Login', 
    'register_now': 'Register Now',
    'login': 'Login',
    'username': 'Username',
    'password': 'Password',
    'email': 'Email',
    'mobile': 'Mobile',
    'location': 'Location',
    'full_name': 'Full Name',
    'name': 'Candidate Name',
    'class': 'Class/Department',
    'submit': 'Add Candidate',
    'back': '← Back to Dashboard',
    'enter_otp': 'Enter OTP',
    'student_login': 'Student Login',
    'student_registration': 'Voter Registration',
    'face_login': 'Face Login',
    'verify_otp': 'Verify OTP',
    'create_profile': 'Create Profile',
    'take_photo': 'Take Photo',
    'election_system': 'Face Login Election System',
    'secure_voting': 'Secure Digital Voting Platform',
    'secure_auth': 'Secure Authentication',
    'otp_face_verify': 'OTP + Face Verification',
    'location_tracking': 'Location Tracking',
    'geo_verification': 'Geo-location Verification',
    'scheduled_voting': 'Scheduled Voting',
    'time_controlled': 'Time-controlled Elections',
    'powered_by': 'Powered by Advanced Face Recognition & Blockchain Technology',
    'add_candidate_title': 'Add New Candidate',
    'candidate_profile_desc': 'Create candidate profiles for the election',
    'profile_photo': 'Profile Photo',
    'description': 'Description',
    'click_upload': 'Click to upload photo',
    'no_file': 'No file chosen',
    'photo_selected': 'Photo selected',
    'enter_full_name': 'Enter full name',
    'enter_class': 'e.g., Computer Science',
    'enter_description': 'Brief description about the candidate',
    'date_of_birth': 'Date of Birth',
    'age': 'Age',
    'gender': 'Gender',
    'select_gender': 'Select Gender',
    'male': 'Male',
    'female': 'Female',
    'other': 'Other',
    'generate': 'Generate',
    'click_button_location': 'Click button to get location'
  },
  kn: {
    'admin_login': 'ನಿರ್ವಾಹಕ ಲಾಗಿನ್',
    'voter_login': 'ಮತದಾರ ಲಾಗಿನ್',
    'register_now': 'ಈಗ ನೋಂದಣಿ ಮಾಡಿ',
    'login': 'ಲಾಗಿನ್',
    'username': 'ಬಳಕೆದಾರ ಹೆಸರು',
    'password': 'ಪಾಸ್ವರ್ಡ್',
    'email': 'ಇಮೇಲ್',
    'mobile': 'ಮೊಬೈಲ್',
    'location': 'ಸ್ಥಳ',
    'full_name': 'ಪೂರ್ಣ ಹೆಸರು',
    'name': 'ಅಭ್ಯರ್ಥಿ ಹೆಸರು',
    'class': 'ವರ್ಗ/ವಿಭಾಗ',
    'submit': 'ಅಭ್ಯರ್ಥಿ ಸೇರಿಸಿ',
    'back': '← ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಹಿಂತಿರುಗಿ',
    'enter_otp': 'OTP ನಮೂದಿಸಿ',
    'student_login': 'ವಿದ್ಯಾರ್ಥಿ ಲಾಗಿನ್',
    'student_registration': 'ಮತದಾರ ನೋಂದಣಿ',
    'face_login': 'ಮುಖ ಲಾಗಿನ್',
    'verify_otp': 'OTP ಪರಿಶೀಲಿಸಿ',
    'create_profile': 'ಪ್ರೊಫೈಲ್ ರಚಿಸಿ',
    'take_photo': 'ಫೋಟೋ ತೆಗೆಯಿರಿ',
    'election_system': 'ಮುಖ ಲಾಗಿನ್ ಚುನಾವಣಾ ವ್ಯವಸ್ಥೆ',
    'secure_voting': 'ಸುರಕ್ಷಿತ ಡಿಜಿಟಲ್ ಮತದಾನ ವೇದಿಕೆ',
    'secure_auth': 'ಸುರಕ್ಷಿತ ದೃಢೀಕರಣ',
    'otp_face_verify': 'OTP + ಮುಖ ಪರಿಶೀಲನೆ',
    'location_tracking': 'ಸ್ಥಳ ಟ್ರ್ಯಾಕಿಂಗ್',
    'geo_verification': 'ಭೌಗೋಳಿಕ ಸ್ಥಳ ಪರಿಶೀಲನೆ',
    'scheduled_voting': 'ನಿಗದಿತ ಮತದಾನ',
    'time_controlled': 'ಸಮಯ-ನಿಯಂತ್ರಿತ ಚುನಾವಣೆಗಳು',
    'powered_by': 'ಸುಧಾರಿತ ಮುಖ ಗುರುತಿಸುವಿಕೆ ಮತ್ತು ಬ್ಲಾಕ್ಚೈನ್ ತಂತ್ರಜ್ಞಾನದಿಂದ ಚಾಲಿತ',
    'add_candidate_title': 'ಹೊಸ ಅಭ್ಯರ್ಥಿ ಸೇರಿಸಿ',
    'candidate_profile_desc': 'ಚುನಾವಣೆಗಾಗಿ ಅಭ್ಯರ್ಥಿ ಪ್ರೊಫೈಲ್‌ಗಳನ್ನು ರಚಿಸಿ',
    'profile_photo': 'ಪ್ರೊಫೈಲ್ ಫೋಟೋ',
    'description': 'ವಿವರಣೆ',
    'click_upload': 'ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಲು ಕ್ಲಿಕ್ ಮಾಡಿ',
    'no_file': 'ಯಾವುದೇ ಫೈಲ್ ಆಯ್ಕೆ ಮಾಡಿಲ್ಲ',
    'photo_selected': 'ಫೋಟೋ ಆಯ್ಕೆ ಮಾಡಲಾಗಿದೆ',
    'enter_full_name': 'ಪೂರ್ಣ ಹೆಸರು ನಮೂದಿಸಿ',
    'enter_class': 'ಉದಾ., ಕಂಪ್ಯೂಟರ್ ಸೈನ್ಸ್',
    'enter_description': 'ಅಭ್ಯರ್ಥಿಯ ಬಗ್ಗೆ ಸಂಕ್ಷಿಪ್ತ ವಿವರಣೆ',
    'date_of_birth': 'ಜನ್ಮ ದಿನಾಂಕ',
    'age': 'ವಯಸ್ಸು',
    'gender': 'ಲಿಂಗ',
    'select_gender': 'ಲಿಂಗ ಆಯ್ಕೆ ಮಾಡಿ',
    'male': 'ಪುರುಷ',
    'female': 'ಮಹಿಳೆ',
    'other': 'ಇತರೆ',
    'generate': 'ಉತ್ಪನ್ನ ಮಾಡಿ',
    'click_button_location': 'ಸ್ಥಳ ಪಡೆಯಲು ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ'
  },
  hi: {
    'admin_login': 'एडमिन लॉगिन',
    'voter_login': 'मतदाता लॉगिन',
    'register_now': 'अभी पंजीकरण करें',
    'login': 'लॉगिन',
    'username': 'यूजरनेम',
    'password': 'पासवर्ड',
    'email': 'ईमेल',
    'mobile': 'मोबाइल',
    'location': 'स्थान',
    'full_name': 'पूरा नाम',
    'name': 'उम्मीदवार का नाम',
    'class': 'कक्षा/विभाग',
    'submit': 'उम्मीदवार जोड़ें',
    'back': '← डैशबोर्ड पर वापस',
    'enter_otp': 'OTP दर्ज करें',
    'student_login': 'छात्र लॉगिन',
    'student_registration': 'मतदाता पंजीकरण',
    'face_login': 'फेस लॉगिन',
    'verify_otp': 'OTP सत्यापित करें',
    'create_profile': 'प्रोफाइल बनाएं',
    'take_photo': 'फोटो लें',
    'election_system': 'फेस लॉगिन चुनाव प्रणाली',
    'secure_voting': 'सुरक्षित डिजिटल मतदान प्लेटफॉर्म',
    'secure_auth': 'सुरक्षित प्रमाणीकरण',
    'otp_face_verify': 'OTP + चेहरा सत्यापन',
    'location_tracking': 'स्थान ट्रैकिंग',
    'geo_verification': 'भू-स्थान सत्यापन',
    'scheduled_voting': 'निर्धारित मतदान',
    'time_controlled': 'समय-नियंत्रित चुनाव',
    'powered_by': 'उन्नत चेहरा पहचान और ब्लॉकचेन प्रौद्योगिकी द्वारा संचालित',
    'add_candidate_title': 'नया उम्मीदवार जोड़ें',
    'candidate_profile_desc': 'चुनाव के लिए उम्मीदवार प्रोफाइल बनाएं',
    'profile_photo': 'प्रोफाइल फोटो',
    'description': 'विवरण',
    'click_upload': 'फोटो अपलोड करने के लिए क्लिक करें',
    'no_file': 'कोई फाइल नहीं चुनी गई',
    'photo_selected': 'फोटो चुनी गई',
    'enter_full_name': 'पूरा नाम दर्ज करें',
    'enter_class': 'जैसे, कंप्यूटर साइंस',
    'enter_description': 'उम्मीदवार के बारे में संक्षिप्त विवरण',
    'date_of_birth': 'जन्म तिथि',
    'age': 'आयु',
    'gender': 'लिंग',
    'select_gender': 'लिंग चुनें',
    'male': 'पुरुष',
    'female': 'महिला',
    'other': 'अन्य',
    'generate': 'जेनरेट करें',
    'click_button_location': 'स्थान पाने के लिए बटन दबाएं'
  }
};

let currentLang = 'en';

function changeLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('selectedLanguage', lang);
  
  // Update all elements with data-translate attribute
  document.querySelectorAll('[data-translate]').forEach(element => {
    const key = element.getAttribute('data-translate');
    const translation = translations[lang][key] || translations['en'][key] || key;
    
    if (element.tagName === 'OPTION') {
      element.textContent = translation;
    } else {
      element.textContent = translation;
    }
  });
  
  // Update placeholders with data-translate-placeholder attribute
  document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
    const key = element.getAttribute('data-translate-placeholder');
    const translation = translations[lang][key] || translations['en'][key] || key;
    element.placeholder = translation;
  });
  
  // Update language selector
  const selector = document.querySelector('select[onchange*="changeLanguage"]');
  if (selector) {
    selector.value = lang;
  }
}

// Make translations globally available
window.translations = translations;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  const savedLang = localStorage.getItem('selectedLanguage') || 'en';
  changeLanguage(savedLang);
});