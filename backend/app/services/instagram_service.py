"""
Pulse — Instagram Graph API Service
Provides live integration with Meta Graph API / Instagram Graph API.
Handles profile discovery, media and comment ingestion, publishing, and insights.
"""

import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("pulse.instagram")

GRAPH_API_VERSION = "v20.0"
FB_GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
IG_GRAPH_BASE = "https://graph.instagram.com"


class InstagramService:
    """Service to interact with Instagram Graph API / Meta APIs."""

    @staticmethod
    async def verify_token_and_get_account(
        access_token: str, account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates the provided Instagram / Meta access token and discovers
        the connected Instagram account details.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. If explicit account_id is provided, try fetching it directly
            if account_id:
                res = await client.get(
                    f"{FB_GRAPH_BASE}/{account_id}",
                    params={
                        "fields": "id,username,name,profile_picture_url,followers_count,follows_count,media_count,biography,website",
                        "access_token": access_token,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "success": True,
                        "account_id": data.get("id"),
                        "username": data.get("username", "instagram_user"),
                        "name": data.get("name", data.get("username", "Instagram User")),
                        "profile_picture_url": data.get("profile_picture_url"),
                        "followers_count": data.get("followers_count", 0),
                        "media_count": data.get("media_count", 0),
                        "biography": data.get("biography", ""),
                        "website": data.get("website", ""),
                        "api_type": "graph_api",
                    }

            # 2. Try fetching via /me/accounts (User Access Token linked to Facebook Pages with connected IG account)
            try:
                me_res = await client.get(
                    f"{FB_GRAPH_BASE}/me",
                    params={
                        "fields": "id,name,accounts{id,name,access_token,instagram_business_account{id,username,name,profile_picture_url,followers_count,media_count,biography,website}}",
                        "access_token": access_token,
                    },
                )
                if me_res.status_code == 200:
                    me_data = me_res.json()
                    accounts = me_data.get("accounts", {}).get("data", [])
                    for page in accounts:
                        ig_acc = page.get("instagram_business_account")
                        if ig_acc:
                            return {
                                "success": True,
                                "account_id": ig_acc.get("id"),
                                "page_id": page.get("id"),
                                "username": ig_acc.get("username", "instagram_user"),
                                "name": ig_acc.get("name", ig_acc.get("username")),
                                "profile_picture_url": ig_acc.get("profile_picture_url"),
                                "followers_count": ig_acc.get("followers_count", 0),
                                "media_count": ig_acc.get("media_count", 0),
                                "biography": ig_acc.get("biography", ""),
                                "website": ig_acc.get("website", ""),
                                "page_access_token": page.get("access_token"),
                                "api_type": "graph_api",
                            }
            except Exception as e:
                logger.warning(f"Error querying /me/accounts: {e}")

            # 3. Try querying /me directly on Instagram Graph API / Basic Display
            try:
                ig_me = await client.get(
                    f"{IG_GRAPH_BASE}/me",
                    params={
                        "fields": "id,username,account_type,media_count",
                        "access_token": access_token,
                    },
                )
                if ig_me.status_code == 200:
                    ig_data = ig_me.json()
                    return {
                        "success": True,
                        "account_id": ig_data.get("id"),
                        "username": ig_data.get("username", "instagram_user"),
                        "name": ig_data.get("username", "Instagram User"),
                        "profile_picture_url": None,
                        "followers_count": 0,
                        "media_count": ig_data.get("media_count", 0),
                        "biography": "",
                        "api_type": "basic_display",
                    }
            except Exception as e:
                logger.warning(f"Error querying ig_graph /me: {e}")

            # 4. Try querying /me directly on FB Graph (direct Page/IG token)
            try:
                fb_me = await client.get(
                    f"{FB_GRAPH_BASE}/me",
                    params={
                        "fields": "id,username,name,profile_picture_url,followers_count,media_count,biography",
                        "access_token": access_token,
                    },
                )
                if fb_me.status_code == 200:
                    fb_data = fb_me.json()
                    return {
                        "success": True,
                        "account_id": fb_data.get("id"),
                        "username": fb_data.get("username", fb_data.get("name", "instagram_user")),
                        "name": fb_data.get("name", "Instagram Account"),
                        "profile_picture_url": fb_data.get("profile_picture_url"),
                        "followers_count": fb_data.get("followers_count", 0),
                        "media_count": fb_data.get("media_count", 0),
                        "biography": fb_data.get("biography", ""),
                        "api_type": "graph_api",
                    }
                else:
                    err_body = fb_me.json() if fb_me.content else {}
                    err_msg = err_body.get("error", {}).get("message", "Invalid access token or insufficient permissions")
                    return {
                        "success": False,
                        "error": err_msg,
                        "status_code": fb_me.status_code,
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to connect to Meta API: {str(e)}",
                }

    @staticmethod
    async def fetch_media_posts(
        access_token: str, account_id: str, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fetches the recent media items (posts, carousels, reels) from Instagram Graph API.
        """
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count"
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Try FB Graph API first
            url = f"{FB_GRAPH_BASE}/{account_id}/media"
            res = await client.get(
                url,
                params={"fields": fields, "limit": limit, "access_token": access_token},
            )
            if res.status_code == 200:
                data = res.json()
                return data.get("data", [])

            # Fallback to basic display media endpoint if FB Graph fails
            url_basic = f"{IG_GRAPH_BASE}/me/media"
            basic_fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
            res_basic = await client.get(
                url_basic,
                params={"fields": basic_fields, "limit": limit, "access_token": access_token},
            )
            if res_basic.status_code == 200:
                data = res_basic.json()
                return data.get("data", [])

            logger.error(f"Failed to fetch media: {res.text}")
            return []

    @staticmethod
    async def fetch_media_comments(
        access_token: str, media_id: str, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fetches comments for a specific Instagram media post.
        """
        fields = "id,text,timestamp,username,like_count,from"
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{FB_GRAPH_BASE}/{media_id}/comments"
            res = await client.get(
                url,
                params={"fields": fields, "limit": limit, "access_token": access_token},
            )
            if res.status_code == 200:
                data = res.json()
                return data.get("data", [])
            logger.warning(f"Could not fetch comments for media {media_id}: {res.text}")
            return []

    @staticmethod
    async def publish_media(
        access_token: str,
        account_id: str,
        caption: str,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publishes an image / carousel / text post using the Instagram Content Publishing API.
        Step 1: Create media container.
        Step 2: Publish media container.
        """
        if not image_url:
            # Instagram Graph API requires an image or video URL for publishing.
            # Use a high quality default fallback placeholder if none provided
            image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Create container
            container_res = await client.post(
                f"{FB_GRAPH_BASE}/{account_id}/media",
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": access_token,
                },
            )
            if container_res.status_code != 200:
                err_data = container_res.json() if container_res.content else {}
                err_msg = err_data.get("error", {}).get("message", "Container creation failed")
                return {"success": False, "error": err_msg}

            creation_id = container_res.json().get("id")
            if not creation_id:
                return {"success": False, "error": "No creation_id returned"}

            # Step 2: Publish container
            publish_res = await client.post(
                f"{FB_GRAPH_BASE}/{account_id}/media_publish",
                params={
                    "creation_id": creation_id,
                    "access_token": access_token,
                },
            )
            if publish_res.status_code != 200:
                err_data = publish_res.json() if publish_res.content else {}
                err_msg = err_data.get("error", {}).get("message", "Publishing failed")
                return {"success": False, "error": err_msg}

            post_id = publish_res.json().get("id")
            return {
                "success": True,
                "post_id": post_id,
                "permalink": f"https://www.instagram.com/p/{post_id}/",
                "published_at": datetime.utcnow().isoformat(),
            }

    @staticmethod
    async def reply_to_comment(
        access_token: str, comment_id: str, message: str
    ) -> Dict[str, Any]:
        """
        Replies directly to an Instagram comment using the Meta Graph API.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{FB_GRAPH_BASE}/{comment_id}/replies"
            res = await client.post(
                url,
                params={"message": message, "access_token": access_token},
            )
            if res.status_code == 200:
                data = res.json()
                return {
                    "success": True,
                    "reply_id": data.get("id"),
                    "sent_at": datetime.utcnow().isoformat(),
                }
            err_data = res.json() if res.content else {}
            err_msg = err_data.get("error", {}).get("message", "Failed to post comment reply")
            return {"success": False, "error": err_msg}

    @staticmethod
    async def get_account_insights(
        access_token: str, account_id: str
    ) -> Dict[str, Any]:
        """
        Fetches 7-day account insights from Instagram Graph API.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{FB_GRAPH_BASE}/{account_id}/insights"
            res = await client.get(
                url,
                params={
                    "metric": "impressions,reach,total_interactions",
                    "period": "day",
                    "metric_type": "total_value",
                    "access_token": access_token,
                },
            )
            if res.status_code == 200:
                return res.json()
            return {}
