import utils

def get_private_check_text(status):
    if status is utils.PlayabilityStatus.PRIVATED:
        return "[{video_id}](https://youtu.be/{video_id}) is privated on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
    elif status is utils.PlayabilityStatus.REMOVED:
        return "[{video_id}](https://youtu.be/{video_id}) is removed on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
    elif status is utils.PlayabilityStatus.COPYRIGHTED:
        return "[{video_id}](https://youtu.be/{video_id}) is copyrighted on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
    elif status is utils.PlayabilityStatus.UNKNOWN:
        return "[{video_id}](https://youtu.be/{video_id}) occurred sth weird on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
    elif status is utils.PlayabilityStatus.MEMBERS_ONLY:
        return "[{video_id}](https://youtu.be/{video_id}) is member-only on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
    elif status is utils.PlayabilityStatus.OFFLINE: # Should not be here though. But I do dumb things.
        return "[{video_id}](https://youtu.be/{video_id}) offlined on [{channel_name}](https://www.youtube.com/channel/{channel_id})."
    else:
        return "[{video_id}](https://youtu.be/{video_id}) occurred sth very weird on [{channel_name}](https://www.youtube.com/channel/{channel_id})."