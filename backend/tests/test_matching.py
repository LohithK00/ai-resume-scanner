from app.services.matcher import score_resume, jd_profile


def test_jd_profile_extracts_skills_and_experience():
    jd = jd_profile('Python developer with 2 years experience in Python, SQL, Flask and machine learning. Bachelor degree preferred.')
    assert jd['experience_years'] == 2.0
    assert 'python' in jd['skills']
    assert 'sql' in jd['skills']


def test_strong_candidate_scores_higher():
    jd = 'Machine Learning Engineer with 2 years experience in Python, SQL, TensorFlow and Flask. Bachelor degree required.'
    strong = {'skills': ['Python', 'SQL', 'TensorFlow', 'Flask', 'Machine Learning'], 'experience_years': 3, 'education': ['B.Tech Computer Science'], 'certifications': []}
    weak = {'skills': ['HTML', 'CSS'], 'experience_years': 0, 'education': [], 'certifications': []}
    a = score_resume(strong, 'Python SQL TensorFlow Flask Machine Learning B.Tech 3 years', jd)
    b = score_resume(weak, 'HTML CSS', jd)
    assert a['final_score'] > b['final_score']
    assert a['recommendation'] in {'STRONG SHORTLIST', 'SHORTLIST'}


def test_missing_skills_are_explainable():
    jd = 'Python, SQL, Docker and AWS developer role.'
    parsed = {'skills': ['Python', 'SQL'], 'experience_years': 1, 'education': [], 'certifications': []}
    result = score_resume(parsed, 'Python SQL', jd)
    assert 'python' in result['matched_skills']
    assert 'docker' in result['missing_skills'] or 'aws' in result['missing_skills']
