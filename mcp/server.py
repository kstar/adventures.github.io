from fastmcp import FastMCP
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, ForeignKey, Index, CheckConstraint, JSON, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import List, Optional, Dict, Union
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
import re
import xml.etree.ElementTree as ET
from math import copysign

class ResolverResult:
    """Class to hold name resolver results"""
    def __init__(self, target: str):
        self.target = target
        self.ra: Optional[float] = None
        self.dec: Optional[float] = None
        self.error: Optional[str] = None
        self.oid: Optional[str] = None
        self.type: Optional[str] = None
        self.primary_designation: str = target

    @classmethod
    def with_error(cls, target: str, error: str) -> 'ResolverResult':
        """Create a ResolverResult instance with an error message."""
        result = cls(target)
        result.error = error
        return result

def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace and normalizing newlines."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def extract_text_from_html(html_content: str) -> Dict[str, str]:
    """Extract clean text from HTML content with basic structure preservation."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extract title
    title = ""
    if soup.title:
        title = clean_text(soup.title.string) if soup.title.string else ""
    
    # Extract main content
    # First try article or main tags
    main_content = soup.find('article') or soup.find('main')
    if not main_content:
        # Fallback to body
        main_content = soup.body if soup.body else soup
    
    # Extract text with basic structure preservation
    paragraphs = []
    for elem in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = clean_text(elem.get_text())
        if text:
            paragraphs.append(text)
    
    content = "\n\n".join(paragraphs)
    
    return {
        "title": title,
        "content": content
    }

def fetch_and_parse_url(url: str) -> Dict[str, str]:
    """Fetch a URL and parse its HTML content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Ensure we're dealing with HTML content
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            return {"error": f"Not an HTML page. Content-Type: {content_type}"}
        
        # Parse the HTML
        parsed = extract_text_from_html(response.text)
        parsed['url'] = url
        return parsed
        
    except requests.RequestException as e:
        return {"error": f"Failed to fetch URL: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing content: {str(e)}"}

# Set up SQLAlchemy
Base = declarative_base()
engine = create_engine('sqlite:////home/akarsh/devel/adventures.github.io/scripts/adventures.db', connect_args={'uri': True})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA query_only = ON")
    cursor.close()


class Object(Base):
    __tablename__ = "objects"
    
    main_id = Column(Text, primary_key=True)
    ra = Column(Float, nullable=False)
    dec = Column(Float, nullable=False)
    type = Column(Text)
    aliases = Column(JSON)
    constellation = Column(Text, nullable=False)
    trixel = Column(Integer, nullable=False)
    
    # Define indexes
    __table_args__ = (
        Index('idx_trixel_on_objects', 'trixel'),
        Index('idx_constellation_on_objects', 'constellation'),
        Index('idx_type_on_objects', 'type')
    )

class Query(Base):
    __tablename__ = "queries"
    
    simbad_id = Column(Text, primary_key=True)
    main_id = Column(Text, nullable=False)

class Displayed(Base):
    __tablename__ = "displayed"
    
    row_id = Column(Integer, primary_key=True)
    display_id = Column(Text, nullable=False)
    main_id = Column(Text, nullable=False)
    
    __table_args__ = (
        Index('unique_display_main', 'display_id', 'main_id', unique=True),
    )

class Mention(Base):
    __tablename__ = "mentions"
    
    mention_id = Column(Integer, primary_key=True)
    filename = Column(Text, nullable=False)
    simbad_id = Column(Text, nullable=False)
    display_id = Column(Text)
    
    __table_args__ = (
        Index('idx_simbad_id_on_mentions', 'simbad_id'),
    )

class Article(Base):
    __tablename__ = "articles"
    
    filename = Column(Text, primary_key=True)
    title = Column(Text)

class Reachability(Base):
    __tablename__ = "reachability"
    
    filename = Column(Text, primary_key=True)
    reachable = Column(Boolean, nullable=False)
    parent = Column(Text)
    
    __table_args__ = (
        CheckConstraint('reachable IN (0, 1)'),
        Index('idx_parent_on_reachability', 'parent')
    )

# Initialize FastMCP
app = FastMCP()

# Example tool that uses the database
@app.tool("list_objects")
async def list_objects(constellation: Optional[str] = None, limit: int = 500) -> List[dict]:
    """
    List astronomical objects, optionally filtered by constellation.
    <IMPORTANT>
    If the constellation is not given as a three-letter IAU standard abbreviation, it must be converted to one.
    </IMPORTANT>

    Arguments:
        limit: The maximum number of objects to return.
        constellation: The constellation to filter by.
    
    Returns:
        A list of objects.
    """
    db = SessionLocal()
    try:
        query = db.query(Object)
        if constellation:
            query = query.filter(Object.constellation == constellation)
        objects = query.limit(limit).all()  # Limiting to `limit` for safety
        return [{
            "main_id": obj.main_id,
            "ra": obj.ra,
            "dec": obj.dec,
            "type": obj.type,
            "constellation": obj.constellation
        } for obj in objects]
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@app.tool("search_objects")
async def search_objects(query: str) -> List[dict]:
    """Search objects by main_id or aliases."""
    db = SessionLocal()
    try:
        objects = db.query(Object).filter(
            (Object.main_id.like(f"%{query}%")) |
            (Object.aliases.like(f"%{query}%"))
        ).limit(50).all()
        return [{
            "main_id": obj.main_id,
            "ra": obj.ra,
            "dec": obj.dec,
            "type": obj.type,
            "constellation": obj.constellation
        } for obj in objects]
    finally:
        db.close()

@app.tool("get_objects_in_article")
async def get_objects_in_article(filename: str) -> List[dict]:
    """Get all astronomical object mentions in a specific article."""
    db = SessionLocal()
    try:
        mentions = db.query(Mention, Object).\
            join(Query, Mention.simbad_id == Query.simbad_id).\
            join(Object, Query.main_id == Object.main_id).\
            filter(Mention.filename == filename).all()
        return [{
            "mention_id": mention.mention_id,
            "display_id": mention.display_id,
            "object": {
                "main_id": obj.main_id,
                "ra": obj.ra,
                "dec": obj.dec,
                "type": obj.type
            }
        } for mention, obj in mentions]
    finally:
        db.close()

@app.tool("get_article_mentions")
async def get_article_mentions(object: str) -> Dict[str, Union[List[str], Optional[str]]]:
    """Get all articles and observing reports mentioning a specific object."""
    db = SessionLocal()
    try:
        # First try to find the object directly in objects table
        obj = db.query(Object).filter(Object.main_id == object).first()
        
        # If not found directly, try resolving it
        if obj is None:
            resolved = resolve_name(object)
            if resolved.error is not None:
                print(f"Error resolving {object}: {resolved.error}")
                return {"articles": [], "error": resolved.error}
            # Try to find the resolved primary designation
            obj = db.query(Object).filter(Object.main_id == resolved.primary_designation).first()
            if obj is None:
                print(f"Resolved object not found in database: {resolved.primary_designation}")
                return {"articles": [], "error": "Object not found in database"}

        # Query the mentioned_objects view directly
        mentions = db.execute(text(
            """SELECT DISTINCT filename FROM mentioned_objects 
               WHERE main_id = :main_id"""),
            {"main_id": obj.main_id}
        ).fetchall()
        
        return {
            'articles': [f'https://adventuresindeepspace.com/{filename[0][:-3] + ".html" if filename[0].endswith(".md") else filename[0]}' for filename in mentions],
            'error': None
        }
    except Exception as e:
        print(f"Error in get_article_mentions: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()
        return {"articles": [], "error": str(e)}
    finally:
        db.close()

@app.tool("get_article_mentions_batch")
async def get_article_mentions_batch(objects: List[str]) -> List[Dict[str, Union[List[str], Optional[str]]]]:
    """Get all articles and observing reports mentioning a list of objects."""
    db = SessionLocal()
    try:
        results = []
        for obj_name in objects:
            # First try to find the object directly in objects table
            obj = db.query(Object).filter(Object.main_id == obj_name).first()
            
            if obj is None:
                results.append({
                    "object": obj_name,
                    "articles": [],
                    "error": "Object not found in database"
                })
                continue

            # Query the mentioned_objects view directly
            mentions = db.execute(text(
                """SELECT DISTINCT filename FROM mentioned_objects 
                   WHERE main_id = :main_id"""),
                {"main_id": obj.main_id}
            ).fetchall()
            
            results.append({
                "object": obj_name,
                "articles": [f'https://adventuresindeepspace.com/{filename[0][:-3] + ".html" if filename[0].endswith(".md") else filename[0]}' for filename in mentions],
                "error": None
            })
            
        return results
    except Exception as e:
        print(f"Error in get_article_mentions_batch: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()
        return [{"object": obj, "articles": [], "error": str(e)} for obj in objects]
    finally:
        db.close()

@app.tool("retrieve_website")
async def retrieve_website(url: str) -> Dict[str, str]:
    """
    Fetch and parse content from a given URL.
    
    Arguments:
        url: The URL to fetch and parse.
    
    Returns:
        A dictionary containing the parsed content with 'title', 'content', and 'url' keys,
        or an 'error' key if something went wrong.
    """
    return fetch_and_parse_url(url)

@app.tool("retrieve_websites")
async def retrieve_websites(urls: List[str]) -> List[Dict[str, str]]:
    """
    Fetch and parse content from multiple URLs in a single call.
    
    Arguments:
        urls: List of URLs to fetch and parse.
    
    Returns:
        A list of dictionaries, each containing the parsed content with 'title', 'content', and 'url' keys,
        or an 'error' key if something went wrong for that URL.
    """
    return [fetch_and_parse_url(url) for url in urls]

def sexagesimal_to_decimal(coord_str: str, is_ra: bool = True) -> float:
    """
    Convert sexagesimal coordinate string to decimal degrees.
    Handles both RA (HH:MM:SS.SS) and Dec (DD:MM:SS.SS) formats.
    """
    parts = coord_str.strip().split(':')
    if len(parts) != 3:
        raise ValueError(f"Invalid coordinate format: {coord_str}")
    
    # Handle negative declinations
    sign = 1
    if not is_ra and parts[0].startswith('-'):
        sign = -1
        parts[0] = parts[0][1:]
    
    try:
        deg = float(parts[0])
        min = float(parts[1])
        sec = float(parts[2])
    except ValueError as e:
        raise ValueError(f"Invalid coordinate parts in {coord_str}: {str(e)}")
    
    if min >= 60 or sec >= 60:
        raise ValueError(f"Invalid minutes/seconds in {coord_str}")
    
    result = abs(deg) + min/60 + sec/3600
    
    # Convert RA from hours to degrees if needed
    if is_ra:
        result *= 15
    
    return copysign(result, sign)

def resolve_name(target: str) -> ResolverResult:
    """
    Resolve an astronomical object name using the CDS SESAME service.
    
    Args:
        target: The name of the astronomical object to resolve
        
    Returns:
        ResolverResult containing the parsed data or error message
    """
    # URL encode the target name
    encoded_target = quote(target)
    url = f"https://cdsweb.u-strasbg.fr/cgi-bin/nph-sesame/-oxFI2/SNVA?{encoded_target}"
    
    try:
        print(f"Fetching URL: {url}")  # Debug log
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        print(f"Response content: {response.content[:500]}")  # Debug log
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Initialize result with target
        result = ResolverResult(target)
        
        # Find Resolver target
        resolver = root.find(".//Resolver")
        print(f"Found resolver: {resolver is not None}")  # Debug log
        
        if resolver is not None:
            primary_designation = resolver.find(".//oname")
            result.primary_designation = primary_designation.text if primary_designation is not None else target
            
            # Get coordinates from decimal degree fields
            jradeg = resolver.find(".//jradeg")
            jdedeg = resolver.find(".//jdedeg")
            
            if jradeg is not None and jdedeg is not None:
                try:
                    result.ra = float(jradeg.text)
                    result.dec = float(jdedeg.text)
                except (ValueError, TypeError) as e:
                    return ResolverResult.with_error(target, f"Could not parse coordinates: {str(e)}")
            
            # Get object type
            otype = resolver.find(".//otype")
            if otype is not None:
                result.type = otype.text
                
            # Get object ID
            oid = resolver.find(".//oid")
            if oid is not None:
                result.oid = oid.text
        
        if result.ra is None or result.dec is None:
            return ResolverResult.with_error(target, "Could not resolve coordinates")
            
        print(f"Final result: {vars(result)}")  # Debug log
        return result
        
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")  # Debug log
        return ResolverResult.with_error(target, f"Request failed: {str(e)}")
    except ET.ParseError as e:
        print(f"XML parsing error: {str(e)}")  # Debug log
        return ResolverResult.with_error(target, f"XML parsing failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()
        return ResolverResult.with_error(target, f"Unexpected error: {str(e)}")

@app.tool("resolve_object")
async def resolve_object(name: str) -> Dict[str, Union[str, float, None]]:
    """
    Resolve an astronomical object name to its coordinates and metadata.
    
    Arguments:
        name: The name of the astronomical object to resolve
    
    Returns:
        Dictionary containing the resolved data including coordinates and metadata,
        or error information if resolution failed.
    """
    try:
        result = resolve_name(name)
        return {
            "target": result.target,
            "ra": result.ra,
            "dec": result.dec,
            "type": result.type,
            "oid": result.oid,
            "primary_designation": result.primary_designation,
            "error": result.error
        }
    except Exception as e:
        print(f"Error in resolve_object: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()
        return {
            "target": name,
            "error": f"Tool error: {str(e)}",
            "ra": None,
            "dec": None,
            "type": None,
            "oid": None,
            "primary_designation": name
        }

if __name__ == "__main__":
    app.run() 