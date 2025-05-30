#!/usr/bin/env zsh
# Script to demonstrate using the ManageAI Resume API with ResumeRebuild

# Use the new server management script
echo "Checking if ManageAI Resume API is running..."
./manage_api_server.py status

# If the server is not running, start it
SERVER_STATUS=$?
if [[ $SERVER_STATUS -ne 0 ]]; then
    echo "ManageAI Resume API is not running. Starting it now..."
    
    # Start the API using the management script
    ./manage_api_server.py start &
    MGMT_PID=$!
    
    # Wait for the server to initialize
    echo "Waiting for API to initialize (this may take 10-15 seconds)..."
    WAIT_TIME=0
    MAX_WAIT=30
    while [[ $WAIT_TIME -lt $MAX_WAIT ]]; do
        sleep 2
        WAIT_TIME=$((WAIT_TIME + 2))
        # Check if server is running
        ./manage_api_server.py status >/dev/null 2>&1
        if [[ $? -eq 0 ]]; then
            echo "ManageAI Resume API is now running."
            # Kill management script but leave the server running
            kill $MGMT_PID 2>/dev/null || true
            break
        fi
        
        echo -n "."
    done
    
    if [[ $WAIT_TIME -ge $MAX_WAIT ]]; then
        echo ""
        echo "ERROR: Server did not start in the expected time."
        echo "Please check the server logs or try again."
        exit 1
    fi
else
    echo "ManageAI Resume API is already running."
fi

# Create a sample resume file if it doesn't exist
if [[ ! -f "sample_resume.txt" ]]; then
    echo "Creating sample resume file..."
    cat > sample_resume.txt << EOF
JOHN DOE
123 Main Street, City, State ZIP | (555) 555-5555 | john.doe@email.com

SUMMARY
Experienced software engineer with a strong background in Python development and web technologies.
Skilled in developing scalable applications and implementing efficient algorithms.

SKILLS
Programming Languages: Python, JavaScript, Java
Web Technologies: React, Django, Flask, HTML, CSS
Tools & Platforms: Git, Docker, AWS, Linux

EXPERIENCE
Senior Software Engineer
ABC Tech Inc., City, State
January 2020 - Present
- Developed and maintained multiple web applications using Python and Django
- Implemented RESTful APIs serving over 10,000 requests per minute
- Led a team of 3 junior developers on a project that reduced processing time by 40%

Software Developer
XYZ Solutions, City, State
June 2017 - December 2019
- Built responsive web interfaces using React and modern JavaScript
- Integrated third-party APIs for payment processing and authentication
- Optimized database queries resulting in 30% faster page load times

EDUCATION
Bachelor of Science in Computer Science
University of Technology, City, State
Graduated: May 2017
EOF
    echo "Sample resume created."
fi

# Create a sample job description file if it doesn't exist
if [[ ! -f "sample_job.txt" ]]; then
    echo "Creating sample job description file..."
    cat > sample_job.txt << EOF
Senior Python Developer

We are seeking an experienced Python Developer to join our growing team. The ideal candidate
will have strong experience with Python, web frameworks like Django or Flask, and database
technologies.

Responsibilities:
- Design and develop high-quality, scalable software solutions
- Write clean, maintainable, and efficient code
- Collaborate with cross-functional teams to define and implement new features
- Troubleshoot and debug applications
- Optimize applications for performance and scalability

Requirements:
- 4+ years of professional experience in Python development
- Strong understanding of web technologies and RESTful APIs
- Experience with Django, Flask, or similar Python web frameworks
- Familiarity with front-end technologies (JavaScript, HTML, CSS)
- Knowledge of relational databases (PostgreSQL, MySQL) and SQL
- Experience with version control systems, particularly Git
- Bachelor's degree in Computer Science or related field (or equivalent experience)
- Strong problem-solving abilities and attention to detail
- Excellent communication skills

Preferred Qualifications:
- Experience with container technologies (Docker, Kubernetes)
- Knowledge of cloud platforms (AWS, GCP, or Azure)
- Familiarity with test-driven development practices
- Experience with Agile development methodologies
- Contributions to open-source projects
EOF
    echo "Sample job description created."
fi

# Run the use_llm_studio.py script with ManageAI integration
echo -e "\nRunning resume analysis using ManageAI Resume API...\n"
python3 use_llm_studio.py --use manageai --api-url http://localhost:8080 --resume sample_resume.txt --job sample_job.txt --action improve

echo -e "\n\nDemonstration completed! You can run more specific commands like:"
echo "  python3 use_llm_studio.py --use manageai --resume sample_resume.txt --job sample_job.txt --action tailor"
echo "  python3 use_llm_studio.py --use manageai --resume sample_resume.txt --action ats"
echo "  python3 use_llm_studio.py --use direct --host localhost --port 5000 --resume sample_resume.txt --action improve"

# Clean up - stop the API if requested
if [[ "$1" == "--cleanup" ]]; then
    echo -e "\nStopping ManageAI Resume API server..."
    ./manage_api_server.py stop
    echo "Server stopped."
else
    echo -e "\nManageAI Resume API server is still running."
    echo "Use './demo_with_managerai.sh --cleanup' to stop it."
fi
