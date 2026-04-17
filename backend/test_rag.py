import os
from dotenv import load_dotenv

# Load environment variables (API Keys)
load_dotenv()

from services.rag_service import ingest_module_content, query_module_content

# The content from your attachment
test_document = """
Group 4 member review

Min Huey: she was alright i guess. had lots of trouble doing stuff assigned to her, so i dont really know how to evaluate her. maybe fusion360 was just not her thing. but then she also didn't take up the opportunity to help do the report either. the only noticeable thing she did was contribute to our team video. during the group presentation, she said nothing. but that is understandable, since you can't say what you don't know.

Danish: very quiet. so i dont know what he does. we let him do the report and tinkercad since he 
doesnt really talk during meetings. but the report was so bad. me and anne had to rewrite 
the whole thing. he didnt do the tinkercad properly so i had to do it. so basically,
he only did the video script. but it was obvious he just read the lines from our report.
i know this because i wrote the final report. also, the
video was only worked on by him and the other 2 in week13. our presentation was in 
week13. i think that says a 
lot about them and the way they do things.

Preethikha: makes excuses that she can't really get anything done/meet up due to upcoming submissions,
unforeseen circumstances, etc. are we not all in uni? is she the only one with assignments?
doesn't really sit right with me. during meetings, she never really does much to help with
the robot, and claims to work on the report. however, i keep seeing her on her phone,
not even doing the report. so nothing gets done. both her and daanish always claim
to work on the report. so why did the unfinalised report turn out so awful? every time we 
call or meet up to review our progress, she loves to say 'oh i wanted to discuss this with 
ya'll before actually starting work on it'. seriously? what kind of excuse is that to not 
show any progress? unbelievable. i really do not see why she deserves to get 
the credit for me and anne's accomplishments. oh and as for what she did, it was just the
video. but as mentioned in my other peer review, this was done the week that the video
was due.

Anne: the backbone of our group. she was the only one that consistently put in effort, took time off
from her busy schedule to help me out with the robot, and cover for the mess that the rest of
the group made. we both have a mutual understanding that we only have each other to rely on,
and if we crumble, so does the rest of our group. we took everything upon ourselves to do all the module's objectives. but there's really only so much that the 2 of us could do. it was a miracle that we managed to get full points on the obstacle course. however, we really could not take up the responsibility for the video due to the robot and video taking such a huge toll on us.
"""

tenant = "ryanc"
module = "cs2030s"

print("Ingesting document...")
ingest_result = ingest_module_content(tenant, module, test_document)
print("Ingest Result:", ingest_result)

print("\nExecuting Query...")
try:
    answer = query_module_content(tenant, module, "What did Anne do in the project?")
    print("\nAnswer generated successfully:")
    print("-" * 50)
    print(answer)
    print("-" * 50)
except Exception as e:
    print("\nError during query generation:")
    import traceback
    traceback.print_exc()
