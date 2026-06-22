import os
import sys
import argparse
import getpass
from twitter_scraper import Twitter_Scraper

try:
    from dotenv import load_dotenv

    print("Loading .env file")
    # Load environment variables, including the new TWITTER_AUTH_TOKEN
    load_dotenv()
    print("Loaded .env file\n")
except Exception as e:
    # Use a more generic error for robustness
    print(f"Warning: Could not load .env file. Proceeding with system environment variables/defaults. Error: {e}")


def main():
    try:
        parser = argparse.ArgumentParser(
            add_help=True,
            usage="python scraper [option] ... [arg] ...",
            description="Twitter Scraper is a tool that allows you to scrape tweets from twitter without using Twitter's API.",
        )

        try:
            # --- AUTH TOKEN ARGUMENT ADDED (CRITICAL) ---
            parser.add_argument(
                "--auth-token",
                type=str,
                default=os.getenv("TWITTER_AUTH_TOKEN"),
                help="Your Twitter authentication token (used for fast, reliable login).",
            )
            # --- Mail/User/Password are kept for __init__ compatibility but won't be used for login ---
            # parser.add_argument(
            #     "--mail",
            #     type=str,
            #     default=os.getenv("TWITTER_MAIL"),
            #     help="Your Twitter mail (auxiliary).",
            # )
            # parser.add_argument(
            #     "--user",
            #     type=str,
            #     default=os.getenv("TWITTER_USERNAME"),
            #     help="Your Twitter username (auxiliary).",
            # )
            # parser.add_argument(
            #     "--password",
            #     type=str,
            #     default=os.getenv("TWITTER_PASSWORD"),
            #     help="Your Twitter password (auxiliary).",
            # )
            # ---------------------------------
            
            parser.add_argument(
                "--headlessState",
                type=str,
                default=os.getenv("HEADLESS"),
                help="Headless mode? [yes/no]"
            )
        except Exception as e:
            print(f"Error retrieving environment variables/defaults: {e}")
            sys.exit(1)

        # --- Remaining arguments (tweets, username, hashtag, etc.) remain unchanged ---
        parser.add_argument(
            "-t",
            "--tweets",
            type=int,
            default=50,
            help="Number of tweets to scrape (default: 50)",
        )

        parser.add_argument(
            "-u",
            "--username",
            type=str,
            default=None,
            help="Twitter username. Scrape tweets from a user's profile.",
        )

        parser.add_argument(
            "-ht",
            "--hashtag",
            type=str,
            default=None,
            help="Twitter hashtag. Scrape tweets from a hashtag.",
        )

        parser.add_argument(
            "--bookmarks",
            action='store_true',
            help="Twitter bookmarks. Scrape tweets from your bookmarks.",
        )

        parser.add_argument(
            "-ntl",
            "--no_tweets_limit",
            nargs='?',
            default=False,
            help="Set no limit to the number of tweets to scrape (will scrap until no more tweets are available).",
        )

        parser.add_argument(
            "-l",
            "--list",
            type=str,
            default=None,
            help="List ID. Scrape tweets from a list.",
        )

        parser.add_argument(
            "-q",
            "--query",
            type=str,
            default=None,
            help="Twitter query or search. Scrape tweets from a query or search.",
        )

        parser.add_argument(
            "-a",
            "--add",
            type=str,
            default="",
            help="Additional data to scrape and save in the .csv file.",
        )

        parser.add_argument(
            "--latest",
            action="store_true",
            help="Scrape latest tweets",
        )

        parser.add_argument(
            "--top",
            action="store_true",
            help="Scrape top tweets",
        )

        args = parser.parse_args()

        # USER_MAIL = args.mail
        # USER_UNAME = args.user
        # USER_PASSWORD = args.password
        HEADLESS_MODE= args.headlessState
        AUTH_TOKEN = args.auth_token # Retrieve the new auth token

        # --- Logic for user input ---
        # if USER_UNAME is None:
        #     # Still prompt for username as a fallback if not provided via CLI or .env, 
        #     # as it is needed for user profile scraping or just for data completeness.
        #     USER_UNAME = input("Twitter Username: ")

        # PASSWORD INPUT REMOVED: Login is strictly by AUTH_TOKEN now.
        
        if HEADLESS_MODE is None:
            headless_input = str(input("Headless? [Yes/No]")).lower()
            HEADLESS_MODE = 'yes' if headless_input in ('y', 'yes') else 'no'


        print()

        tweet_type_args = []
        if args.username is not None:
            tweet_type_args.append(args.username)
        if args.hashtag is not None:
            tweet_type_args.append(args.hashtag)
        if args.list is not None:
            tweet_type_args.append(args.list)
        if args.query is not None:
            tweet_type_args.append(args.query)
        # Note: args.bookmarks is boolean, not added to list check above
        if args.bookmarks is not False:
            tweet_type_args.append("bookmarks")


        additional_data: list = args.add.split(",")

        if len(tweet_type_args) > 1:
            print("Please specify only one of --username, --hashtag, --bookmarks, --list, or --query.")
            sys.exit(1)

        if args.latest and args.top:
            print("Please specify either --latest or --top. Not both.")
            sys.exit(1)

        # --- CRITICAL CHANGE: Check for AUTH_TOKEN first ---
        if AUTH_TOKEN is None:
            print("\n❌ Login failed: The '--auth-token' argument or 'TWITTER_AUTH_TOKEN' environment variable is required.")
            print("Please retrieve your current auth token and provide it.")
            sys.exit(1)

        # --- Initialize Scraper and Pass Auth Token ---
        if AUTH_TOKEN is not None:
            scraper = Twitter_Scraper(
                # mail=USER_MAIL,
                # username=USER_UNAME,
                # password=USER_PASSWORD, # Will not be used for login
                headlessState=HEADLESS_MODE,
                auth_token=AUTH_TOKEN, # Pass the token to the scraper
            )
            scraper.login() # This now performs token injection
            scraper.scrape_tweets(
                max_tweets=args.tweets,
                # Simplify boolean check for nargs='?'
                no_tweets_limit=True if args.no_tweets_limit is not False else False,
                scrape_username=args.username,
                scrape_hashtag=args.hashtag,
                scrape_bookmarks=args.bookmarks,
                scrape_query=args.query,
                scrape_list=args.list,
                scrape_latest=args.latest,
                scrape_top=args.top,
                scrape_poster_details="pd" in additional_data,
            )
            scraper.save_to_csv()
            if not scraper.interrupted:
                scraper.close()
        else:
            print(
                "Missing Twitter username. Please check your arguments or .env file."
            )
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nScript Interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        # Attempt to close the driver if an unexpected error occurred
        if 'scraper' in locals() and hasattr(scraper, 'driver') and scraper.driver:
            scraper.close()
        sys.exit(1)
    
    sys.exit(0) # Exit with status code 0 on successful completion


if __name__ == "__main__":
    main()