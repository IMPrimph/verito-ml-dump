import nltk
from nltk.tokenize import word_tokenize
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
        
        # Define rating thresholds with a wider neutral range
        self.RATING_THRESHOLD_HIGH = 7
        self.RATING_THRESHOLD_LOW = 4
        
        # Define common themes and their related keywords
        self.themes = {
            # Work Culture themes
            'work_culture': {
                'positive': ['collaborative', 'inclusive', 'supportive', 'friendly', 'positive'],
                'negative': ['toxic', 'hostile', 'political', 'bureaucratic', 'unfriendly'],
                'neutral': ['formal', 'casual', 'traditional', 'startup-like', 'corporate']
            },
            'leadership': {
                'positive': ['transparent', 'inspiring', 'approachable', 'effective', 'visionary'],
                'negative': ['micromanaging', 'unclear', 'disorganized', 'absent', 'poor'],
                'neutral': ['hands-off', 'structured', 'hierarchical', 'decentralized']
            },
            'compensation': {
                'positive': ['competitive', 'generous', 'excellent', 'comprehensive', 'above-market'],
                'negative': ['low', 'below-market', 'inadequate', 'unfair', 'poor'],
                'neutral': ['standard', 'industry-average', 'market-rate', 'typical']
            },
            'work_life_balance': {
                'positive': ['flexible', 'balanced', 'accommodating', 'reasonable', 'great'],
                'negative': ['demanding', 'stressful', 'burnout', 'overwhelming', 'poor'],
                'neutral': ['structured', 'predictable', 'regular', 'standard']
            },
            'career_growth': {
                'positive': ['excellent', 'promising', 'abundant', 'clear', 'supported'],
                'negative': ['limited', 'stagnant', 'unclear', 'rare', 'nonexistent'],
                'neutral': ['steady', 'gradual', 'traditional', 'standard']
            },
            'innovation': {
                'positive': ['cutting-edge', 'innovative', 'advanced', 'modern', 'progressive'],
                'negative': ['outdated', 'legacy', 'behind', 'obsolete', 'stagnant'],
                'neutral': ['established', 'stable', 'conventional', 'standard']
            }
        }

    def _analyze_numeric_ratings(self, review: Dict) -> Dict[str, str]:
        """Analyze numeric ratings with more nuanced categorization"""
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
                    else:
                        themes[theme] = 'neutral'  # Explicitly handle neutral ratings
            
        return themes

    def _analyze_salary_range(self, salary_range: str, currency: str, location: str = None) -> str:
        """Analyze salary with context-aware thresholds"""
        if not salary_range or not currency:
            return 'neutral'
            
        try:
            # Extract numeric values from salary range
            values = [int(''.join(filter(str.isdigit, val))) 
                     for val in salary_range.split('-')]
            
            if len(values) == 2:
                avg_salary = sum(values) / 2
                
                # Add location-based adjustment (example thresholds)
                if location and 'remote' in location.lower():
                    high_threshold = 90000  # Adjusted for remote
                    low_threshold = 45000
                else:
                    high_threshold = 100000
                    low_threshold = 50000
                
                if avg_salary > high_threshold:
                    return 'positive'
                elif avg_salary < low_threshold:
                    return 'negative'
                return 'neutral'
            return 'neutral'
        except:
            return 'neutral'

    def _analyze_text(self, text: str) -> Tuple[Dict[str, List[str]], str]:
        """Enhanced text analysis with sentiment-specific keyword matching"""
        if not text:
            return {}, 'neutral'
            
        text_lower = text.lower()
        words = word_tokenize(text_lower)
        
        # Get overall sentiment
        sentiment_scores = self.sia.polarity_scores(text)
        if sentiment_scores['compound'] >= 0.05:
            overall_sentiment = 'positive'
        elif sentiment_scores['compound'] <= -0.05:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
            
        # Find themes with sentiment-specific matching
        identified_themes = defaultdict(list)
        for theme, sentiment_keywords in self.themes.items():
            for sentiment, keywords in sentiment_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    identified_themes[sentiment].append(theme)
                
        return identified_themes, overall_sentiment

    def analyze_review(self, review: Dict) -> Dict[str, List[str]]:
        """Enhanced review analysis with better neutral detection"""
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
        if 'compensation_range' in review:
            salary_sentiment = self._analyze_salary_range(
                review['compensation_range'], 
                review.get('currency', 'USD'),
                review.get('location', None)
            )
            result[salary_sentiment].append('compensation')
        
        # Analyze text content with context awareness
        text_fields = {
            'headline': None,  # None means use detected sentiment
            'pros': 'positive',  # Force positive sentiment
            'cons': 'negative'   # Force negative sentiment
        }
        
        for field, forced_sentiment in text_fields.items():
            if field in review and review[field]:
                themes_by_sentiment, detected_sentiment = self._analyze_text(review[field])
                
                # Use forced sentiment if specified, otherwise use detected
                sentiment_to_use = forced_sentiment if forced_sentiment else detected_sentiment
                
                # Add themes to appropriate sentiment categories
                for sentiment, themes in themes_by_sentiment.items():
                    for theme in themes:
                        if forced_sentiment:
                            result[forced_sentiment].append(theme)
                        else:
                            result[sentiment].append(theme)
        
        # Remove duplicates and sort
        for sentiment in result:
            result[sentiment] = sorted(list(set(result[sentiment])))
        
        return result

    def _generate_theme_text(self, theme: str, percentage: float) -> str:
        """Generate balanced theme text descriptions"""
        theme_texts = {
            # Core workplace aspects
            'work_culture': 'Company culture and work environment',
            'leadership': 'Leadership and management approach',
            'compensation': 'Compensation and benefits package',
            'work_life_balance': 'Work-life balance practices',
            'career_growth': 'Career development opportunities',
            'innovation': 'Innovation and technological advancement',
            
            # Additional neutral-focused descriptions
            'work_structure': 'Organizational structure and processes',
            'company_size': 'Company size and operational scale',
            'industry_position': 'Position within the industry',
            'market_focus': 'Market focus and business approach',
            'project_complexity': 'Project scope and complexity',
            'team_structure': 'Team organization and dynamics',
            'communication_style': 'Communication patterns and practices',
            'decision_making': 'Decision-making processes',
            'change_management': 'Approach to change and adaptation',
            'work_pace': 'Work pace and delivery expectations'
        }
        
        return f"{theme_texts.get(theme, theme.replace('_', ' ').title())} ({percentage:.1f}% of reviews)"

    def generate_summary(self, reviews: List[Dict]) -> Dict:
        """Generate summary with balanced sentiment distribution"""
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
        
        # Calculate percentages with more nuanced thresholds
        total_reviews = len(reviews)
        theme_sentiments = {}
        
        # Get all unique themes
        all_unique_themes = set()
        for sentiment in ['positive', 'negative', 'neutral']:
            all_unique_themes.update(all_themes[sentiment].keys())
            
        # More nuanced sentiment determination
        for theme in all_unique_themes:
            pos_count = all_themes['positive'].get(theme, 0)
            neg_count = all_themes['negative'].get(theme, 0)
            neu_count = all_themes['neutral'].get(theme, 0)
            
            # Calculate percentages
            pos_pct = (pos_count / total_reviews) * 100
            neg_pct = (neg_count / total_reviews) * 100
            neu_pct = (neu_count / total_reviews) * 100
            
            # More balanced sentiment determination
            if max(pos_pct, neg_pct) < 30 or abs(pos_pct - neg_pct) < 15:
                dominant = 'neutral'
                percentage = neu_pct + min(pos_pct, neg_pct)
            elif pos_pct > neg_pct:
                dominant = 'positive'
                percentage = pos_pct
            else:
                dominant = 'negative'
                percentage = neg_pct
                
            # Include themes that appear in at least 15% of reviews
            if percentage >= 15:
                theme_sentiments[theme] = (dominant, percentage)
        
        # Prepare final summary
        summary = {
            'positive': [],
            'negative': [],
            'neutral': []
        }
        
        # Add themes to their dominant sentiment category
        for theme, (sentiment, percentage) in theme_sentiments.items():
            theme_text = self._generate_theme_text(theme, percentage)
            summary[sentiment].append(theme_text)
            
        # Sort each category by percentage
        for sentiment in summary:
            summary[sentiment] = sorted(
                summary[sentiment],
                key=lambda x: float(x.split('(')[1].rstrip('% of reviews)')),
                reverse=True
            )
        
        return summary

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