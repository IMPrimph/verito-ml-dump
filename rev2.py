import nltk
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import defaultdict
from typing import List, Dict, Tuple

class CompanyReviewAnalyzer:
    def __init__(self):
        # Download required NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('vader_lexicon', quiet=True)

        # Initialize NLP tools
        self.sia = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))

        # Define rating thresholds
        self.RATING_THRESHOLD_HIGH = 7
        self.RATING_THRESHOLD_LOW = 4

        # Define common themes and their related keywords
        self.themes = {
            'work_culture': [
                'culture', 'environment', 'atmosphere', 'workplace', 'team', 'collaboration',
                'friendly', 'inclusive', 'diverse', 'supportive', 'transparency', 'ethics',
                'values', 'diversity', 'inclusion', 'respect', 'belonging', 'community',
                'social', 'fun', 'positive', 'toxic', 'politics', 'bureaucracy'
            ],
            'leadership': [
                'leadership', 'management', 'direction', 'strategy', 'vision', 'leader',
                'manager', 'executive', 'boss', 'supervisor', 'communication', 'transparency',
                'decision', 'guidance', 'mentorship', 'coaching', 'feedback', 'recognition',
                'micromanagement', 'hierarchy', 'direction', 'clarity'
            ],
            'compensation': [
                'salary', 'benefits', 'pay', 'compensation', 'bonus', 'package', 'stock',
                'insurance', 'retirement', '401k', 'raise', 'equity', 'options', 'rsu',
                'healthcare', 'dental', 'vision', 'pto', 'vacation', 'leave', 'perks',
                'allowance', 'reimbursement', 'overtime', 'commission'
            ],
            'work_life_balance': [
                'balance', 'flexibility', 'hours', 'schedule', 'remote', 'time',
                'wlb', 'flexible', 'workload', 'overtime', 'vacation', 'burnout',
                'stress', 'pressure', 'deadline', 'weekend', 'holiday', 'family',
                'personal', 'hybrid', 'work from home', 'wfh', 'commute'
            ],
            'career_growth': [
                'growth', 'learning', 'development', 'opportunity', 'promotion', 'career',
                'training', 'mentor', 'skill', 'advance', 'progress', 'education',
                'certification', 'conference', 'workshop', 'upskill', 'challenge',
                'responsibility', 'exposure', 'path', 'trajectory', 'potential'
            ],
            'innovation': [
                'innovation', 'technology', 'creative', 'innovative', 'cutting-edge', 'modern',
                'tools', 'tech', 'startup', 'agile', 'future', 'research', 'development',
                'experimentation', 'breakthrough', 'transformation', 'digital', 'automation',
                'ai', 'machine learning', 'cloud', 'stack'
            ],
            'job_security': [
                'security', 'stable', 'stability', 'layoff', 'redundancy', 'permanent',
                'contract', 'temporary', 'future', 'uncertainty', 'downsizing', 'reorganization',
                'restructuring', 'merger', 'acquisition', 'full-time', 'part-time'
            ],
            'office_environment': [
                'office', 'workspace', 'facility', 'amenities', 'location', 'parking',
                'cafeteria', 'food', 'gym', 'ergonomic', 'desk', 'equipment', 'supplies',
                'building', 'infrastructure', 'safety', 'clean', 'comfortable'
            ],
            'team_dynamics': [
                'team', 'colleague', 'coworker', 'peer', 'collaboration', 'communication',
                'support', 'morale', 'conflict', 'politics', 'drama', 'cooperation',
                'teamwork', 'relationship', 'dynamic', 'interaction', 'coordination'
            ],
            'company_performance': [
                'performance', 'growth', 'revenue', 'profit', 'market', 'competitor',
                'industry', 'success', 'failure', 'strategy', 'direction', 'leadership',
                'management', 'vision', 'mission', 'goal', 'objective', 'target'
            ],
            'diversity_inclusion': [
                'diversity', 'inclusion', 'equality', 'equity', 'discrimination', 'bias',
                'harassment', 'representation', 'minority', 'gender', 'race', 'age',
                'disability', 'lgbt', 'culture', 'background', 'perspective'
            ],
            'project_management': [
                'project', 'deadline', 'timeline', 'planning', 'execution', 'delivery',
                'scrum', 'agile', 'waterfall', 'methodology', 'process', 'workflow',
                'coordination', 'organization', 'requirement', 'specification'
            ]
        }

    def _analyze_numeric_ratings(self, review: Dict) -> Dict[str, str]:
        """Analyze numeric ratings and categorize them"""
        themes = {}

        rating_fields = {
            'work_life_balance': 'work_life_balance',
            'career_growth': 'career_growth',
            'leadership_management': 'leadership',
            'innovation': 'innovation'
        }

        for field, theme in rating_fields.items():
            if field in review:
                rating = review[field]
                if isinstance(rating, (int, float)):
                    if rating >= self.RATING_THRESHOLD_HIGH:
                        themes[theme] = 'positive'
                    elif rating <= self.RATING_THRESHOLD_LOW:
                        themes[theme] = 'negative'

        return themes

    def _analyze_salary_range(self, salary_range: str, currency: str) -> str:
        """Analyze if the salary is competitive based on market data"""
        if not salary_range or not currency:
            return 'neutral'

        try:
            # Extract numeric values from salary range
            values = [int(''.join(filter(str.isdigit, val)))
                     for val in salary_range.split('-')]

            if len(values) == 2:
                avg_salary = sum(values) / 2
                if avg_salary > 100000:
                    return 'positive'
                elif avg_salary < 50000:
                    return 'negative'
            return 'neutral'
        except:
            return 'neutral'

    def _analyze_text(self, text: str) -> Tuple[List[str], str]:
        """Analyze text content and return identified themes and sentiment"""
        if not text:
            return [], 'neutral'

        text_lower = text.lower()

        # Get sentiment
        sentiment_scores = self.sia.polarity_scores(text)
        if sentiment_scores['compound'] >= 0.05:
            sentiment = 'positive'
        elif sentiment_scores['compound'] <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # Find themes
        identified_themes = []
        for theme, keywords in self.themes.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_themes.append(theme)

        return identified_themes, sentiment

    def analyze_review(self, review: Dict) -> Dict[str, List[str]]:
        """Main method to analyze a single review and categorize themes"""
        result = {
            'positive': [],
            'negative': [],
            'neutral': []
        }

        # Analyze numeric ratings
        rating_themes = self._analyze_numeric_ratings(review)
        for theme, sentiment in rating_themes.items():
            result[sentiment].append(theme)

        # Analyze salary and benefits
        if 'compensation_range' in review and 'currency' in review:
            salary_sentiment = self._analyze_salary_range(
                review['compensation_range'],
                review['currency']
            )
            result[salary_sentiment].append('compensation')

        # Analyze text content (headline, pros, cons)
        text_fields = ['headline', 'pros', 'cons']
        for field in text_fields:
            if field in review and review[field]:
                themes, sentiment = self._analyze_text(review[field])
                for theme in themes:
                    if field == 'pros':
                        result['positive'].append(theme)
                    elif field == 'cons':
                        result['negative'].append(theme)
                    else:
                        result[sentiment].append(theme)

        # Remove duplicates and sort
        result['positive'] = sorted(list(set(result['positive'])))
        result['negative'] = sorted(list(set(result['negative'])))
        result['neutral'] = sorted(list(set(result['neutral'])))

        return result


    def generate_summary(self, reviews: List[Dict]) -> Dict:
        """Generate a comprehensive summary from multiple reviews"""
        all_themes = {
            'positive': defaultdict(int),
            'negative': defaultdict(int),
            'neutral': defaultdict(int)
        }

        # Analyze each review
        for review in reviews:
            analysis = self.analyze_review(review)
            for sentiment, themes in analysis.items():
                for theme in themes:
                    all_themes[sentiment][theme] += 1

        # Calculate percentages and determine dominant sentiment for each theme
        total_reviews = len(reviews)
        theme_sentiments = {}

        # Get all unique themes
        all_unique_themes = set()
        for sentiment in ['positive', 'negative', 'neutral']:
            all_unique_themes.update(all_themes[sentiment].keys())

        # For each theme, determine its dominant sentiment
        for theme in all_unique_themes:
            pos_count = all_themes['positive'].get(theme, 0)
            neg_count = all_themes['negative'].get(theme, 0)
            neu_count = all_themes['neutral'].get(theme, 0)

            # Calculate percentages
            pos_pct = (pos_count / total_reviews) * 100
            neg_pct = (neg_count / total_reviews) * 100
            neu_pct = (neu_count / total_reviews) * 100

            # Determine dominant sentiment
            max_pct = max(pos_pct, neg_pct, neu_pct)

            # In case of a tie, prefer stronger sentiments (positive/negative) over neutral
            if max_pct == pos_pct and max_pct > 0:
                dominant = 'positive'
                percentage = pos_pct
            elif max_pct == neg_pct and max_pct > 0:
                dominant = 'negative'
                percentage = neg_pct
            else:
                dominant = 'neutral'
                percentage = neu_pct

            # Only include themes that appear in at least 20% of reviews
            if max_pct >= 20:
                theme_sentiments[theme] = (dominant, percentage)

        # Prepare final summary with themes in their dominant categories only
        summary = {
            'positive': [],
            'negative': [],
            'neutral': []
        }

        # Add themes to their dominant sentiment category
        for theme, (sentiment, percentage) in theme_sentiments.items():
            theme_text = self._generate_theme_text(theme, percentage)
            summary[sentiment].append(theme_text)

        # Sort each category by percentage (descending)
        for sentiment in summary:
            summary[sentiment] = sorted(
                summary[sentiment],
                key=lambda x: float(x.split('(')[1].rstrip('% of reviews)')),
                reverse=True
            )

        return summary

    def _generate_theme_text(self, theme: str, percentage: float) -> str:
        """Generate human-readable theme text with expanded categories"""
        theme_texts = {
            # Workplace Culture & Environment
            'work_culture': 'Strong company culture and positive work environment',
            'diversity': 'Inclusive workplace with strong diversity initiatives',
            'ethics': 'Strong ethical practices and corporate values',
            'social_impact': 'Meaningful social impact and community engagement',
            'collaboration': 'Collaborative and team-oriented environment',

            # Leadership & Management
            'leadership': 'Effective leadership and management team',
            'communication': 'Clear communication and transparency from management',
            'strategy': 'Strong strategic direction and company vision',
            'mentorship': 'Quality mentorship and professional guidance',
            'recognition': 'Good employee recognition and appreciation practices',

            # Compensation & Benefits
            'compensation': 'Competitive compensation and benefits package',
            'equity': 'Attractive equity and stock options',
            'healthcare': 'Comprehensive healthcare and wellness benefits',
            'retirement': 'Strong retirement and financial benefits',
            'perks': 'Valuable workplace perks and amenities',

            # Work-Life Balance
            'work_life_balance': 'Good work-life balance and flexible scheduling',
            'remote_work': 'Effective remote work policies and support',
            'time_off': 'Generous vacation and time-off policies',
            'workload': 'Manageable workload and reasonable expectations',
            'flexibility': 'Flexible work arrangements and scheduling',

            # Career Development
            'career_growth': 'Excellent career growth and learning opportunities',
            'training': 'Comprehensive training and development programs',
            'skills_development': 'Strong focus on skills development and learning',
            'promotion': 'Clear promotion paths and advancement opportunities',
            'education': 'Good educational benefits and learning resources',

            # Job Content & Innovation
            'innovation': 'Strong focus on innovation and modern technologies',
            'project_variety': 'Diverse and interesting project opportunities',
            'creativity': 'Encouragement of creativity and new ideas',
            'tools': 'Access to modern tools and technologies',
            'autonomy': 'High degree of autonomy and decision-making freedom',

            # Office & Resources
            'office_environment': 'Well-designed and comfortable office space',
            'equipment': 'High-quality equipment and resources',
            'location': 'Convenient office location and accessibility',
            'facilities': 'Great office facilities and amenities',
            'safety': 'Strong workplace safety and security measures',

            # Team & Coworkers
            'team_quality': 'High-caliber colleagues and strong team dynamics',
            'peer_support': 'Supportive peer relationships and teamwork',
            'team_spirit': 'Strong team spirit and camaraderie',
            'knowledge_sharing': 'Good knowledge sharing and collaboration',
            'team_diversity': 'Diverse and inclusive team composition',

            # Company Stability & Growth
            'company_stability': 'Strong company stability and market position',
            'growth_potential': 'Excellent company growth and future prospects',
            'job_security': 'Good job security and stability',
            'market_position': 'Strong market presence and industry standing',
            'financial_health': 'Solid financial performance and stability',

            # Client & Project Management
            'client_relations': 'Positive client relationships and interactions',
            'project_management': 'Effective project management practices',
            'deadlines': 'Reasonable deadlines and project timelines',
            'client_quality': 'High-quality clients and project opportunities',
            'workflow': 'Efficient workflow and processes'
        }

        return f"{theme_texts.get(theme, theme.replace('_', ' ').title())} ({percentage:.1f}% of reviews)"

# Example usage
if __name__ == "__main__":
    # Initialize the analyzer
    analyzer = CompanyReviewAnalyzer()

    # Sample reviews
    reviews = [
        {
            'headline': 'Great tech company with amazing benefits',
            'overall_rating': 5,
            'work_life_balance': 9,
            'compensation_range': '150000-200000',
            'currency': 'USD',
            'career_growth': 8,
            'leadership_management': 7,
            'innovation': 9,
            'pros': 'Cutting-edge technology, excellent benefits package including equity, strong emphasis on work-life balance. Regular team events and great office amenities. Leadership is transparent and communicative.',
            'cons': 'Sometimes projects can be challenging with tight deadlines. Growing pains as company scales.'
        },
        {
            'headline': 'Good company but needs improvement in management',
            'overall_rating': 3,
            'work_life_balance': 6,
            'compensation_range': '80000-100000',
            'currency': 'USD',
            'career_growth': 5,
            'leadership_management': 4,
            'innovation': 7,
            'pros': 'Decent pay, good healthcare benefits, some interesting projects',
            'cons': 'Poor management decisions, lack of clear career path, office politics'
        },
        {
            'headline': 'Inclusive workplace with growth opportunities',
            'overall_rating': 4,
            'work_life_balance': 8,
            'compensation_range': '120000-140000',
            'currency': 'USD',
            'career_growth': 9,
            'leadership_management': 8,
            'innovation': 7,
            'pros': 'Strong diversity initiatives, great learning opportunities, supportive teammates',
            'cons': 'Work can be intense during peak seasons'
        },
        {
            'headline': 'Stable job but outdated technology',
            'overall_rating': 3,
            'work_life_balance': 7,
            'compensation_range': '90000-110000',
            'currency': 'USD',
            'career_growth': 5,
            'leadership_management': 6,
            'innovation': 3,
            'pros': 'Job security, good work-life balance, friendly colleagues',
            'cons': 'Old technology stack, slow to adopt new tools, bureaucratic processes'
        },
        {
            'headline': 'Fast-paced startup with great potential',
            'overall_rating': 4,
            'work_life_balance': 5,
            'compensation_range': '130000-160000',
            'currency': 'USD',
            'career_growth': 9,
            'leadership_management': 7,
            'innovation': 9,
            'pros': 'Cutting-edge projects, equity potential, great team culture, lots of learning',
            'cons': 'Long hours, some uncertainty about future direction'
        },
        {
            'headline': 'Remote-first company with strong culture',
            'overall_rating': 5,
            'work_life_balance': 9,
            'compensation_range': '140000-170000',
            'currency': 'USD',
            'career_growth': 8,
            'leadership_management': 8,
            'innovation': 8,
            'pros': 'Flexible remote work, great tools for collaboration, strong emphasis on work-life balance',
            'cons': 'Sometimes miss in-person interactions, communication can be challenging across time zones'
        },
        {
            'headline': 'Good benefits but high stress environment',
            'overall_rating': 3,
            'work_life_balance': 4,
            'compensation_range': '110000-130000',
            'currency': 'USD',
            'career_growth': 7,
            'leadership_management': 5,
            'innovation': 6,
            'pros': 'Competitive salary, good healthcare, interesting technical challenges',
            'cons': 'Constant deadlines, burnout issues, poor project management'
        },
        {
            'headline': 'Excellent learning environment for juniors',
            'overall_rating': 4,
            'work_life_balance': 8,
            'compensation_range': '70000-90000',
            'currency': 'USD',
            'career_growth': 9,
            'leadership_management': 8,
            'innovation': 7,
            'pros': 'Great mentorship program, structured learning path, supportive seniors',
            'cons': 'Below market compensation, basic office amenities'
        }
    ]

    # Analyze single review
    print("\nSingle Review Analysis:")
    single_analysis = analyzer.analyze_review(reviews[0])
    print(single_analysis)

    # Generate summary for all reviews
    print("\nOverall Summary:")
    summary = analyzer.generate_summary(reviews)
    print(summary)