import os

from jinja2 import Environment, FileSystemLoader

from utils import UTF8_ENCODING

REPORTS_DIR = 'reports'
os.makedirs(REPORTS_DIR, exist_ok=True)

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('quiz_results.html')

def create_progress_report(user_stats: dict) -> None:
    ip_address = user_stats['ip_address']
    quizzes = user_stats['quizzes']

    html_output = template.render(ip_address=ip_address, quizzes=quizzes)
    print(f'{html_output=}')

    outfile_path = f'{REPORTS_DIR}/Progress Report for {ip_address}.html'
    with open(outfile_path, 'w', encoding=UTF8_ENCODING) as f:
        f.write(html_output)

    print(f'Saved: {outfile_path}')
    return outfile_path

if __name__ == '__main__':
    user_stats = {
        "ip_address": "99.198.232.98",
        "quizzes": [
            {
                "article": "A 15-year consolidated overview of data in over 6000 patients from the Transthyretin Amyloidosis Outcomes Survey (THAOS)",
                "question": "What is the most prevalent genotype enrolled in THAOS patients in Europe, South America, and Japan?",
                "answer": "a. ATTRwt amyloidosis",
                "correct": False,
                "time_seconds": {
                    "$numberInt": "1735077720"
                },
                "formatted_time": "2024-12-24 10:02 PM UTC"
            },
            {
                "article": "A 15-year consolidated overview of data in over 6000 patients from the Transthyretin Amyloidosis Outcomes Survey (THAOS)",
                "question": "What is the most prevalent genotype enrolled in THAOS patients in Europe, South America, and Japan?",
                "answer": "b. V122I (p.V142I)",
                "correct": False,
                "time_seconds": {
                    "$numberInt": "1735077723"
                },
                "formatted_time": "2024-12-24 10:02 PM UTC"
            },
            {
                "article": "A 15-year consolidated overview of data in over 6000 patients from the Transthyretin Amyloidosis Outcomes Survey (THAOS)",
                "question": "What is the most prevalent genotype enrolled in THAOS patients in Europe, South America, and Japan?",
                "answer": "c. V30M",
                "correct": True,
                "time_seconds": {
                    "$numberInt": "1735077726"
                },
                "formatted_time": "2024-12-24 10:02 PM UTC"
            },
            {
                "article": "A 1-year analysis of adverse events following COVID-19 vaccination in Lebanon: a retrospective study",
                "question": "According to the study, what was the most common systemic Adverse Event Following Immunization (AEFI) reported with the Pfizer-BioNTech (PZ) vaccine?",
                "answer": "c. Headache",
                "correct": False,
                "time_seconds": {
                    "$numberInt": "1735077781"
                },
                "formatted_time": "2024-12-24 10:03 PM UTC"
            },
            {
                "article": "A 1-year analysis of adverse events following COVID-19 vaccination in Lebanon: a retrospective study",
                "question": "According to the study, what was the most common systemic Adverse Event Following Immunization (AEFI) reported with the Pfizer-BioNTech (PZ) vaccine?",
                "answer": "a. Fatigue",
                "correct": False,
                "time_seconds": {
                    "$numberInt": "1735077784"
                },
                "formatted_time": "2024-12-24 10:03 PM UTC"
            },
            {
                "article": "A 1-year analysis of adverse events following COVID-19 vaccination in Lebanon: a retrospective study",
                "question": "According to the study, what was the most common systemic Adverse Event Following Immunization (AEFI) reported with the Pfizer-BioNTech (PZ) vaccine?",
                "answer": "b. General body pain",
                "correct": True,
                "time_seconds": {
                    "$numberInt": "1735077788"
                },
                "formatted_time": "2024-12-24 10:03 PM UTC"
            }
        ]
    }
    report_file = create_progress_report(user_stats)
    pass
