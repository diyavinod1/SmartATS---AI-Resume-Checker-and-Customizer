from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import re
import json
from collections import Counter
import math

app = Flask(__name__)
CORS(app)

class ResumeAnalyzer:
    def __init__(self):
        self.skill_keywords = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'typescript'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'django', 'flask', 'node.js', 'express', 'spring', 'next.js', 'nuxt.js'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'dynamodb', 'cassandra'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ci/cd', 'jenkins', 'gitlab', 'ansible'],
            'data_science': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'r', 'scikit-learn', 'keras'],
            'mobile': ['android', 'ios', 'react native', 'flutter', 'xamarin', 'swiftui'],
            'tools': ['git', 'jira', 'confluence', 'slack', 'figma', 'photoshop', 'illustrator', 'vs code', 'intellij'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking', 'agile', 'scrum']
        }
        
        self.job_titles = [
            'software engineer', 'web developer', 'frontend developer', 'backend developer', 'full stack developer',
            'data scientist', 'machine learning engineer', 'devops engineer', 'cloud engineer', 'mobile developer',
            'product manager', 'project manager', 'ui ux designer', 'data analyst', 'business analyst',
            'system administrator', 'network engineer', 'security engineer', 'qa engineer', 'test engineer'
        ]
        
        self.industries = [
            'technology', 'finance', 'healthcare', 'e-commerce', 'education', 'manufacturing',
            'consulting', 'telecommunications', 'media', 'entertainment', 'retail', 'automotive'
        ]
    
    def extract_keywords(self, text):
        """Extract keywords from text"""
        words = re.findall(r'\b[a-zA-Z0-9+#]+\b', text.lower())
        return set(words)
    
    def calculate_ats_score(self, resume_text, job_description):
        """Calculate ATS compatibility score with detailed breakdown"""
        resume_words = self.extract_keywords(resume_text)
        job_words = self.extract_keywords(job_description)
        
        if not job_words:
            return 0, {"keyword": 0, "skill": 0, "structure": 0}
        
        # Calculate keyword match (60% of total score)
        matched_keywords = resume_words.intersection(job_words)
        keyword_score = min((len(matched_keywords) / len(job_words)) * 60, 60)
        
        # Calculate skill match (25% of total score)
        skill_score = self.calculate_skill_match(resume_text, job_description)
        
        # Calculate structure score (15% of total score)
        structure_score = self.calculate_structure_score(resume_text)
        
        total_score = min(keyword_score + skill_score + structure_score, 100)
        
        # Return detailed breakdown for stats
        breakdown = {
            "keyword": round(keyword_score),
            "skill": round(skill_score),
            "structure": round(structure_score)
        }
        
        return round(total_score), breakdown
    
    def calculate_skill_match(self, resume_text, job_description):
        """Calculate skill matching score"""
        resume_skills = self.extract_skills(resume_text)
        job_skills = self.extract_skills(job_description)
        
        if not job_skills:
            return 25
        
        matched_skills = resume_skills.intersection(job_skills)
        skill_match_ratio = len(matched_skills) / len(job_skills)
        
        # Enhanced scoring: more weight for critical skills
        critical_skills = self.identify_critical_skills(job_description)
        critical_match = len(resume_skills.intersection(critical_skills))
        critical_bonus = min(critical_match * 2, 10)  # Bonus for critical skills
        
        base_score = skill_match_ratio * 25
        return min(base_score + critical_bonus, 25)
    
    def identify_critical_skills(self, job_description):
        """Identify critical skills from job description"""
        critical_indicators = ['required', 'must have', 'essential', 'mandatory', 'necessary']
        job_lower = job_description.lower()
        critical_skills = set()
        
        for skill_category, skills in self.skill_keywords.items():
            for skill in skills:
                # Check if skill is mentioned near critical indicators
                skill_pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(skill_pattern, job_lower):
                    # Look for critical indicators in surrounding context
                    words_around = re.findall(r'\b\w+\b', job_lower[max(0, job_lower.find(skill)-100):job_lower.find(skill)+100])
                    if any(indicator in words_around for indicator in critical_indicators):
                        critical_skills.add(skill)
        
        return critical_skills
    
    def extract_skills(self, text):
        """Extract skills from text with improved matching"""
        text_lower = text.lower()
        skills_found = set()
        
        for category, skill_list in self.skill_keywords.items():
            for skill in skill_list:
                # Use word boundaries for exact matching
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    skills_found.add(skill)
        
        return skills_found
    
    def calculate_structure_score(self, resume_text):
        """Calculate resume structure score with enhanced criteria"""
        score = 0
        resume_lower = resume_text.lower()
        
        # Check for essential sections (30 points)
        essential_sections = ['experience', 'education', 'skills']
        optional_sections = ['projects', 'certifications', 'achievements', 'summary']
        
        essential_found = sum(1 for section in essential_sections if section in resume_lower)
        optional_found = sum(1 for section in optional_sections if section in resume_lower)
        
        score += (essential_found / len(essential_sections)) * 20
        score += min(optional_found * 2, 10)  # Bonus for optional sections
        
        # Check length (optimal 400-800 words) - 20 points
        word_count = len(re.findall(r'\b\w+\b', resume_text))
        if 400 <= word_count <= 800:
            score += 15
        elif 300 <= word_count < 400 or 800 < word_count <= 1000:
            score += 10
        else:
            score += 5
        
        # Check for contact info - 10 points
        contact_patterns = [
            r'\b[\w\.-]+@[\w\.-]+\.\w+\b',  # email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # phone
            r'\bhttps?://[^\s]+',  # portfolio/linkedin
            r'\blinkedin\.com/in/[^\s]+'  # linkedin profile
        ]
        contact_found = sum(1 for pattern in contact_patterns if re.search(pattern, resume_text, re.IGNORECASE))
        score += min(contact_found * 2.5, 10)
        
        # Check for quantifiable achievements - 10 points
        quant_patterns = [
            r'\d+%', r'\$\d+', r'\d+\+', r'increased by', r'reduced by', 
            r'saved \$\d+', r'improved by', r'managed \d+', r'led \d+'
        ]
        quant_found = any(re.search(pattern, resume_text, re.IGNORECASE) for pattern in quant_patterns)
        if quant_found:
            score += 10
        
        return min(score, 15)  # Cap structure score at 15% of total
    
    def generate_recommendations(self, resume_text, job_description, current_score):
        """Generate comprehensive improvement recommendations"""
        recommendations = []
        
        # Analyze missing skills with priority
        missing_skills_recommendation = self.analyze_missing_skills(resume_text, job_description)
        if missing_skills_recommendation:
            recommendations.append(missing_skills_recommendation)
        
        # Analyze certifications
        certifications_recommendation = self.analyze_certifications(resume_text, job_description)
        if certifications_recommendation:
            recommendations.append(certifications_recommendation)
        
        # Analyze content length and structure
        content_recommendation = self.analyze_content_structure(resume_text)
        if content_recommendation:
            recommendations.append(content_recommendation)
        
        # Analyze quantifiable achievements
        achievements_recommendation = self.analyze_achievements(resume_text)
        if achievements_recommendation:
            recommendations.append(achievements_recommendation)
        
        # Analyze keyword optimization
        keyword_recommendation = self.analyze_keywords(resume_text, job_description)
        if keyword_recommendation:
            recommendations.append(keyword_recommendation)
        
        # Analyze contact information
        contact_recommendation = self.analyze_contact_info(resume_text)
        if contact_recommendation:
            recommendations.append(contact_recommendation)
        
        # Analyze section organization
        section_recommendation = self.analyze_sections(resume_text)
        if section_recommendation:
            recommendations.append(section_recommendation)
        
        return recommendations
    
    def analyze_missing_skills(self, resume_text, job_description):
        """Analyze and recommend missing skills"""
        resume_skills = self.extract_skills(resume_text)
        job_skills = self.extract_skills(job_description)
        missing_skills = job_skills - resume_skills
        
        if not missing_skills:
            return None
        
        critical_skills = self.identify_critical_skills(job_description)
        high_priority_skills = missing_skills.intersection(critical_skills)
        medium_priority_skills = missing_skills - high_priority_skills
        
        if high_priority_skills:
            return {
                'type': 'skills',
                'title': 'Add Critical Missing Skills',
                'description': f'These skills are explicitly required in the job description: {", ".join(sorted(high_priority_skills)[:5])}. Consider gaining experience or certifications in these areas.',
                'priority': 'high'
            }
        elif medium_priority_skills:
            return {
                'type': 'skills',
                'title': 'Add Recommended Skills',
                'description': f'These skills are mentioned in the job description: {", ".join(sorted(medium_priority_skills)[:5])}. Adding these will improve your match score.',
                'priority': 'medium'
            }
        
        return None
    
    def analyze_certifications(self, resume_text, job_description):
        """Analyze certifications"""
        resume_lower = resume_text.lower()
        job_lower = job_description.lower()
        
        # Look for certification mentions in job description
        cert_keywords = ['certification', 'certified', 'certificate', 'license', 'credential']
        cert_mentioned = any(keyword in job_lower for keyword in cert_keywords)
        
        has_certifications = any(keyword in resume_lower for keyword in cert_keywords)
        
        if cert_mentioned and not has_certifications:
            # Identify relevant certifications from job description
            relevant_certs = []
            for cert_keyword in cert_keywords:
                if cert_keyword in job_lower:
                    # Extract context around certification mentions
                    cert_context = re.findall(rf'\b\w+\s+\w+\s+{re.escape(cert_keyword)}|\b{re.escape(cert_keyword)}\s+\w+\s+\w+', job_lower)
                    relevant_certs.extend(cert_context)
            
            cert_examples = ", ".join(set(relevant_certs))[:3] if relevant_certs else "industry-relevant"
            
            return {
                'type': 'certifications',
                'title': 'Add Relevant Certifications',
                'description': f'The job description mentions certifications. Consider adding {cert_examples} certifications to improve your credibility.',
                'priority': 'medium'
            }
        
        return None
    
    def analyze_content_structure(self, resume_text):
        """Analyze content length and structure"""
        word_count = len(re.findall(r'\b\w+\b', resume_text))
        
        if word_count < 300:
            return {
                'type': 'content',
                'title': 'Expand Resume Content',
                'description': f'Your resume is quite short ({word_count} words). Optimal resumes are 400-800 words. Add more details about your experiences, projects, and achievements.',
                'priority': 'high'
            }
        elif word_count > 1000:
            return {
                'type': 'content',
                'title': 'Condense Resume Content',
                'description': f'Your resume is lengthy ({word_count} words). Consider making it more concise (optimal: 400-800 words) by removing less relevant information.',
                'priority': 'medium'
            }
        
        return None
    
    def analyze_achievements(self, resume_text):
        """Analyze quantifiable achievements"""
        quant_patterns = [
            r'\d+%', r'\$\d+', r'\d+\+', r'increased by', r'reduced by', 
            r'saved \$\d+', r'improved by', r'managed \d+', r'led \d+',
            r'achieved \d+', r'reduced by \d+', r'increased from.*to.*\d+'
        ]
        
        has_quantifiable = any(re.search(pattern, resume_text, re.IGNORECASE) for pattern in quant_patterns)
        
        if not has_quantifiable:
            return {
                'type': 'achievements',
                'title': 'Add Quantifiable Achievements',
                'description': 'Include numbers and metrics to showcase your impact. Examples: "Increased sales by 20%", "Reduced costs by $50K", "Managed a team of 10 people".',
                'priority': 'high'
            }
        
        return None
    
    def analyze_keywords(self, resume_text, job_description):
        """Analyze keyword optimization"""
        resume_keywords = self.extract_keywords(resume_text)
        job_keywords = self.extract_keywords(job_description)
        missing_keywords = job_keywords - resume_keywords
        
        if missing_keywords and len(missing_keywords) > 5:
            # Get the most frequent missing keywords (excluding common words)
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            important_missing = [kw for kw in missing_keywords if kw not in common_words and len(kw) > 2][:8]
            
            if important_missing:
                return {
                    'type': 'keywords',
                    'title': 'Optimize Keywords',
                    'description': f'Include these important keywords from the job description: {", ".join(important_missing)}. This will significantly improve your ATS score.',
                    'priority': 'high'
                }
        
        return None
    
    def analyze_contact_info(self, resume_text):
        """Analyze contact information completeness"""
        contact_patterns = {
            'email': r'\b[\w\.-]+@[\w\.-]+\.\w+\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'linkedin': r'\blinkedin\.com/in/[^\s]+',
            'portfolio': r'\bhttps?://[^\s]+(?<!linkedin\.com)'
        }
        
        missing_contacts = []
        for contact_type, pattern in contact_patterns.items():
            if not re.search(pattern, resume_text, re.IGNORECASE):
                missing_contacts.append(contact_type)
        
        if missing_contacts:
            return {
                'type': 'contact',
                'title': 'Add Missing Contact Information',
                'description': f'Consider adding your {", ".join(missing_contacts)} to make it easier for recruiters to contact you.',
                'priority': 'low'
            }
        
        return None
    
    def analyze_sections(self, resume_text):
        """Analyze resume sections organization"""
        resume_lower = resume_text.lower()
        essential_sections = ['experience', 'education', 'skills']
        missing_sections = [section for section in essential_sections if section not in resume_lower]
        
        if missing_sections:
            return {
                'type': 'sections',
                'title': 'Add Essential Sections',
                'description': f'Your resume is missing these important sections: {", ".join(missing_sections)}. Add these to improve readability and ATS parsing.',
                'priority': 'high'
            }
        
        return None

    def generate_linkedin_suggestions(self, resume_text, job_description):
        """Generate LinkedIn optimization suggestions"""
        suggestions = {}
        
        # Extract key information from resume
        skills = self.extract_skills(resume_text)
        job_skills = self.extract_skills(job_description)
        resume_lower = resume_text.lower()
        
        # Generate LinkedIn Headline suggestions
        suggestions['headline'] = self.generate_headline_suggestions(resume_text, job_description, skills, job_skills)
        
        # Generate LinkedIn About section suggestions
        suggestions['about'] = self.generate_about_suggestions(resume_text, job_description, skills)
        
        # Generate LinkedIn Featured Skills suggestions
        suggestions['skills'] = self.generate_skills_suggestions(skills, job_skills)
        
        # Generate LinkedIn Recommendations
        suggestions['recommendations'] = self.generate_linkedin_recommendations(resume_text, job_description)
        
        return suggestions
    
    def generate_headline_suggestions(self, resume_text, job_description, skills, job_skills):
        """Generate LinkedIn headline suggestions"""
        headlines = []
        
        # Extract potential job titles from resume and job description
        resume_titles = [title for title in self.job_titles if title in resume_text.lower()]
        job_titles_found = [title for title in self.job_titles if title in job_description.lower()]
        
        # Get top skills that match job requirements
        matching_skills = skills.intersection(job_skills)
        top_skills = list(matching_skills)[:3] if matching_skills else list(skills)[:3]
        
        # Headline 1: Professional title + key skills
        if resume_titles:
            title = resume_titles[0].title()
            if top_skills:
                headlines.append(f"{title} | {', '.join([s.title() for s in top_skills])} | Open to New Opportunities")
            else:
                headlines.append(f"{title} | Seeking New Challenges | Open to Opportunities")
        
        # Headline 2: Focus on job target
        if job_titles_found:
            target_title = job_titles_found[0].title()
            headlines.append(f"{target_title} | {', '.join([s.title() for s in top_skills[:2]])} | Passionate About Innovation")
        
        # Headline 3: Achievement focused
        quant_patterns = [r'increased by \d+%', r'reduced by \d+%', r'managed \d+', r'led \d+']
        achievements = []
        for pattern in quant_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            achievements.extend(matches[:2])
        
        if achievements and resume_titles:
            achievement_text = " | ".join(achievements[:2])
            headlines.append(f"{resume_titles[0].title()} | {achievement_text} | Results-Driven Professional")
        
        # Headline 4: Industry focused
        industries_found = [industry for industry in self.industries if industry in job_description.lower()]
        if industries_found and top_skills:
            industry = industries_found[0].title()
            headlines.append(f"{industry} Professional | {', '.join([s.title() for s in top_skills])} | Strategic Thinker")
        
        # Fallback headline
        if not headlines:
            headlines.append("Experienced Professional | Skilled in Multiple Technologies | Open to New Opportunities")
        
        return headlines[:4]  # Return top 4 headlines
    
    def generate_about_suggestions(self, resume_text, job_description, skills):
        """Generate LinkedIn About section suggestions"""
        about_sections = []
        
        # Extract key information
        experience_years = self.extract_experience_years(resume_text)
        top_skills = list(skills)[:8]
        industries = [industry for industry in self.industries if industry in job_description.lower()]
        
        # Template 1: Professional summary
        summary = f"Experienced professional with {experience_years} of experience in "
        if industries:
            summary += f"the {industries[0]} industry. "
        else:
            summary += "technology and innovation. "
        
        summary += f"Skilled in {', '.join([s.title() for s in top_skills[:4]])}. "
        summary += "Passionate about delivering high-quality solutions and driving business growth through technology."
        about_sections.append(summary)
        
        # Template 2: Achievement focused
        achievement_template = f"Results-driven professional with {experience_years} years of experience specializing in "
        if top_skills:
            achievement_template += f"{', '.join([s.title() for s in top_skills[:3]])}. "
        
        achievement_template += "Proven track record of delivering innovative solutions and exceeding expectations. "
        achievement_template += "Currently seeking new challenges where I can leverage my expertise to drive success."
        about_sections.append(achievement_template)
        
        # Template 3: Future focused
        future_template = f"Forward-thinking professional with {experience_years} years of experience in "
        if industries:
            future_template += f"{industries[0]}. "
        
        future_template += f"Expertise in {', '.join([s.title() for s in top_skills[:5]])}. "
        future_template += "Committed to continuous learning and staying at the forefront of industry trends. "
        future_template += "Open to connecting and exploring new opportunities."
        about_sections.append(future_template)
        
        return about_sections[:3]
    
    def generate_skills_suggestions(self, skills, job_skills):
        """Generate LinkedIn skills suggestions"""
        suggestions = {}
        
        # Top skills to feature (mix of your skills and job-required skills)
        your_top_skills = list(skills)[:10]
        job_top_skills = list(job_skills)[:10]
        
        # Combine and prioritize skills that appear in both
        combined_skills = set(your_top_skills + job_top_skills)
        prioritized_skills = []
        
        # Add skills that are in both first
        common_skills = skills.intersection(job_skills)
        prioritized_skills.extend(list(common_skills)[:5])
        
        # Add remaining skills
        remaining_skills = combined_skills - common_skills
        prioritized_skills.extend(list(remaining_skills)[:10 - len(prioritized_skills)])
        
        suggestions['featured_skills'] = [skill.title() for skill in prioritized_skills[:10]]
        
        # Skills to consider adding
        missing_important_skills = job_skills - skills
        suggestions['skills_to_add'] = [skill.title() for skill in list(missing_important_skills)[:5]]
        
        return suggestions
    
    def generate_linkedin_recommendations(self, resume_text, job_description):
        """Generate LinkedIn profile recommendations"""
        recommendations = []
        
        # Check for profile completeness indicators
        has_education = 'education' in resume_text.lower()
        has_experience = 'experience' in resume_text.lower()
        has_skills = len(self.extract_skills(resume_text)) > 0
        
        # Recommendation 1: Profile photo
        recommendations.append({
            'title': 'Add a Professional Profile Photo',
            'description': 'A professional headshot can increase profile views by 14x. Use a clear, recent photo with good lighting.',
            'priority': 'high'
        })
        
        # Recommendation 2: Custom URL
        recommendations.append({
            'title': 'Customize Your LinkedIn URL',
            'description': 'Create a custom LinkedIn URL (e.g., linkedin.com/in/yourname) for better professional branding.',
            'priority': 'medium'
        })
        
        # Recommendation 3: Background photo
        recommendations.append({
            'title': 'Add a Background Photo',
            'description': 'Use a relevant background image that reflects your industry or professional interests.',
            'priority': 'low'
        })
        
        # Content-based recommendations
        if not has_education:
            recommendations.append({
                'title': 'Complete Education Section',
                'description': 'Add your educational background to build credibility and help recruiters understand your qualifications.',
                'priority': 'high'
            })
        
        if not has_experience:
            recommendations.append({
                'title': 'Detail Your Experience',
                'description': 'Add comprehensive experience details with achievements and responsibilities for each role.',
                'priority': 'high'
            })
        
        if not has_skills:
            recommendations.append({
                'title': 'Add Relevant Skills',
                'description': 'Include at least 10-15 relevant skills and get endorsements from colleagues.',
                'priority': 'high'
            })
        
        # Engagement recommendations
        recommendations.append({
            'title': 'Engage with Industry Content',
            'description': 'Regularly share and engage with relevant industry content to increase your visibility.',
            'priority': 'medium'
        })
        
        return recommendations
    
    def extract_experience_years(self, resume_text):
        """Extract years of experience from resume"""
        # Look for year patterns and dates
        year_pattern = r'(19|20)\d{2}'
        years = re.findall(year_pattern, resume_text)
        
        if len(years) >= 2:
            try:
                years_numeric = [int(year) for year in years if 1900 <= int(year) <= 2030]
                if years_numeric:
                    experience = max(years_numeric) - min(years_numeric)
                    return min(experience, 30)  # Cap at 30 years
            except:
                pass
        
        # Fallback: estimate based on content length and structure
        word_count = len(re.findall(r'\b\w+\b', resume_text))
        if word_count > 800:
            return "5+"
        elif word_count > 500:
            return "3-5"
        elif word_count > 300:
            return "1-3"
        else:
            return "1"

analyzer = ResumeAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        data = request.get_json()
        resume_text = data.get('resume', '')
        job_description = data.get('job_description', '')
        
        if not resume_text or not job_description:
            return jsonify({'error': 'Resume and job description are required'}), 400
        
        # Calculate ATS score with detailed breakdown
        ats_score, score_breakdown = analyzer.calculate_ats_score(resume_text, job_description)
        
        return jsonify({
            'ats_score': ats_score,
            'score_breakdown': score_breakdown
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        resume_text = data.get('resume', '')
        job_description = data.get('job_description', '')
        current_score = data.get('current_score', 0)
        
        if not resume_text or not job_description:
            return jsonify({'error': 'Resume and job description are required'}), 400
        
        # Generate comprehensive recommendations
        recommendations = analyzer.generate_recommendations(resume_text, job_description, current_score)
        
        return jsonify({
            'recommendations': recommendations
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/linkedin-suggestions', methods=['POST'])
def get_linkedin_suggestions():
    try:
        data = request.get_json()
        resume_text = data.get('resume', '')
        job_description = data.get('job_description', '')
        
        if not resume_text or not job_description:
            return jsonify({'error': 'Resume and job description are required'}), 400
        
        # Generate LinkedIn optimization suggestions
        linkedin_suggestions = analyzer.generate_linkedin_suggestions(resume_text, job_description)
        
        return jsonify({
            'linkedin_suggestions': linkedin_suggestions
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)