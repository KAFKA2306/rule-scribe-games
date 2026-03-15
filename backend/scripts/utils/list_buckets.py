import os
import sys

sys.path.append(os.getcwd())
try:
    from app.core import supabase
except ImportError as e:
    print(f"Error importing supabase client: {e}")
    sys.exit(1)


def list_buckets():
    try:
        res = supabase.supabase.storage.list_buckets()
        print("Buckets found:")
        for bucket in res:
            print(f"- {bucket.name}")
    except Exception as e:
        print(f"Error listing buckets: {e}")


if __name__ == "__main__":
    list_buckets()
