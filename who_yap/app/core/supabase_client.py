from supabase import create_client, Client
from .config import SupabaseConfig

supabase: Client = create_client(SupabaseConfig.SUPABASE_URL, SupabaseConfig.SUPABASE_KEY) 