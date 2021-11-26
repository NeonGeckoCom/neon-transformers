# Neon Transformers

## About

### Utterance Transformers

A utterance transformer takes `utterances` and a `context` as input, 
then returns the modified `utterances` and a new `context`

`context` is simply a python dictionary, it can contain anything

A transformer might change the utterances or simply return them unmodified with a `context`

eg. 
- The translator transformer will detect language and translate as necessary, it returns modified utterances
- the NER transformer return unmodified utterances and the context contains extracted entities

#### mycroft integration

Usage with mycroft-core is limited to skills, it is useful for fallback and common_qa skills

You can import individual transformers directly in skills

#### neon integration

neon-core integrate the neon_transformers service in the nlp pipeline transparently

- neon_transformers are integrated into mycroft after STT but before Intent parsing
- all enabled transformer plugins (mycroft.conf) are loaded
- each plugin has a priority that the developer sets and the user can override (mycroft.conf)
- utterances are passed to each transformer sequentially
  - utterances are replaced with the text returned by a transformer
  - if utterances are transformed, the next transformer receives the transformed utterances
  - context is merged with context returned by previous transformer
- the transformed utterances are passed to the intent stage 
- context is available in message.context for skills during intent handling
  - skills can add transformers to their requirements.txt
  - for compatibility with vanilla mycroft-core skills should handle message.context as optional data
  - if a certain transformer is absolutely necessary, load it directly if message.context is missing data

#### ovos-core integration

WIP - not available

### Audio Transformers

TODO