try:
    from bs4 import BeautifulSoup
    import auth, utl

    Auth = auth.Auth()
    UTL = utl.Utl()

    season = input("Enter season URL: ")
    while not UTL.check_season_url_format(season):
        print("Invalid season URL format. Please try again.")
        season = input("Enter season URL: ")

    UTL.selected_language_code = input("Enter language code: ")
    while not UTL.check_lanauge_code(UTL.selected_language_code):
        print("Invalid language code. Please try again.")
        UTL.selected_language_code = input("Enter language code: ")


    episodes = UTL.get_episodes_list(BeautifulSoup(Auth.request(season).content, 'html.parser'))

    for translation in UTL.translations:
        if translation['episodeNumber'] in episodes.keys():
            print("Processing episode " + translation['episodeNumber'] + " ...")
            form = UTL.build_episode_translate_form(BeautifulSoup(Auth.request(episodes[translation['episodeNumber']]['translate_url']).content, 'html.parser'), 
                                                        title=translation['episodeTitle'], 
                                                        description=translation['description'])
            response = Auth.update_episode(form_data=form)
            if response.status_code == 200:
                print("Episode " + translation['episodeNumber'] + " translated successfully.")
    input('Press Enter to close this window...')
    
except Exception as e:
    print(e)
    input('Press Enter to close this window...')


