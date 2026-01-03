# Blackboard - Download Course Materials

## Purpose
Download course materials from Blackboard courses into an organized folder structure.

## Prerequisites
- Credentials saved: `Cred: blackboard`
- Logged into Blackboard (UTMB)

## Steps
1. Navigate to https://utmb.blackboard.com/
2. Log in using saved credentials (if not already logged in)
3. Navigate to Courses page
4. For each course (or specified courses):
   - Open the course
   - Navigate to Course Content/Materials section
   - Identify downloadable files (PDFs, documents, etc.)
   - Download files to organized folder structure:
     ```
     Downloads/Blackboard/
       CourseName/
         Materials/
           Week1/
           Week2/
           ...
     ```
5. Track downloaded files to avoid duplicates

## Folder Structure
```
Downloads/Blackboard/
  {Course Name}/
    Materials/
      {Week/Module Name}/
        {filename}
    Assignments/
      {Assignment Name}/
        {filename}
```

## Implementation Notes
- Use browser automation to navigate courses
- Parse course structure to organize downloads
- Create folder structure automatically
- Skip files that already exist (check by name/size)
- Handle multiple file types (PDF, DOC, PPT, etc.)

## Usage
```
Auto: download materials from my Blackboard courses
Auto: download materials from [Course Name] in Blackboard
```

