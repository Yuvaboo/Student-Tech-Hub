import os
import requests

def get_youtube_links(skills: list[str]) -> dict:
    """
    Searches YouTube Data API for the top 3 beginner videos for each skill.
    Uses caching (in-memory dict) to avoid quota limits.
    """
    API_KEY = os.getenv("YOUTUBE_API_KEY")
    if not API_KEY:
        # Return mock links if API key is not set
        return {skill: [{"title": f"Learn {skill} for Beginners", "url": f"https://youtube.com/results?search_query={skill}+tutorial"}] for skill in skills}
    
    results = {}
    
    # In-memory simple cache
    if not hasattr(get_youtube_links, "cache"):
        get_youtube_links.cache = {}
        
    for skill in skills:
        if skill in get_youtube_links.cache:
            results[skill] = get_youtube_links.cache[skill]
            continue
            
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": f"{skill} tutorial for beginners",
            "type": "video",
            "maxResults": 3,
            "key": API_KEY
        }
        try:
            response = requests.get(url, params=params)
            data = response.json()
            videos = []
            if "items" in data:
                for item in data["items"]:
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    videos.append({
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    })
            results[skill] = videos
            get_youtube_links.cache[skill] = videos
        except Exception as e:
            print(f"YouTube API error: {e}")
            results[skill] = []
            
    return results
