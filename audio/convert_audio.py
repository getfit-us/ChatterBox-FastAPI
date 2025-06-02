from pydub import AudioSegment






def join_audio_files(input_paths, output_path):
    # Concatenate audio files with a 50ms crossfade between segments
    if not input_paths:
        raise ValueError("No input audio files provided.")
    audio_segments = [AudioSegment.from_file(path) for path in input_paths]
    combined_audio = audio_segments[0]
    for segment in audio_segments[1:]:
        combined_audio = combined_audio.append(segment, crossfade=50)
    combined_audio.export(output_path, format="wav")
    
    
    
    
