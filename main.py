#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import os
import sys

### Class Definitions
class FrameElement:
    def __init__(self, fe_name, index, is_target=False):
        self.fe_name = fe_name
        self.indices = [index]
        self.is_target = is_target
    def append_index(self, index):
        self.indices.append(index)
    def __repr__(self):
        return f'{self.fe_name}[{self.is_target} target]: {self.indices}\n'

class FrameDescription:
    def __init__(self):
        self.frame_name = ""
        self.frame_elements = {}
    def set_frame_name(self, frame_name):
        self.frame_name = frame_name
    def set_LU(self, lex_unit, lu_pos):
        self.lex_unit = lex_unit
        self.lu_pos = lu_pos
        self.frame_elements[lex_unit] = FrameElement(lex_unit, lu_pos, True)
    def add_FE(self, fe_name, index):
        if fe_name[1]=='-':
            fe_name = fe_name[2:]
        if fe_name in self.frame_elements:
            self.frame_elements[fe_name].append_index(index)
        else:
            self.frame_elements[fe_name] = FrameElement(fe_name, index)
        """
        if fe_name in self.frame_elements:
            self.frame_elements[fe_name].append(index)
        else:
            self.frame_elements[fe_name] = [index]
        """
    def __bool__(self):
        return bool(self.frame_name or self.frame_elements)
class Sentence:
    def __init__(self, sentence_id):
        self.sentence_id = sentence_id
        self.words = []
        self.pos_list = []
        self.frame_descriptions = {}
    def add_word(self, word):
        self.words.append(word)
    def add_pos(self, pos):
        self.pos_list.append(pos)
    def add_frame(self, frame_description):
        self.frame_descriptions[frame_description.frame_name] = frame_description
    def __str__(self):
        output_str = f"{self.sentence_id}: {' '.join(self.words)}\n"
        output_str += f"{' '.join(self.pos_list)}"
        for fname in self.frame_descriptions.keys():
            output_str += f'{fname}: {self.frame_descriptions[fname].lex_unit} ({self.frame_descriptions[fname].lu_pos})\n'
            output_str += f'\t{self.frame_descriptions[fname].frame_elements}\n'
            #output_str += '\n'
        #output_str += f"{[self.frame_descriptions[fname].frame_name for fname in self.frame_descriptions.keys()]}"
        return output_str

if len(sys.argv) == 2:
    conll = pd.read_csv(sys.argv[1], header=None, sep='\t')
    conll.columns = ["word_index", "word_form", "?", "lemma", "?", "pos", "sent_num", "?", "?", "?", "?", "?", "lemma_POS", "frame_name", "FE_Name_BIO"]
    #columns_to_drop = [2, 4, 6, 7, 8, 9, 10, 11]
    conll.drop('?', axis='columns', inplace=True)

    sentences = []
    current_frame = FrameDescription()
    current_sentence = Sentence(0)
    for row in conll.itertuples(name="LU_labelled"):
        # if current word is first in its sentence
        if int(row.word_index) == 1:
            # store found frame into prev sentence
            if current_frame:
                current_sentence.add_frame(current_frame)
                current_frame = FrameDescription()
            # if last saved sentence exists and it shares same id
            if len(sentences) > 0 and sentences[-1].sentence_id == int(row.sent_num):
                current_sentence = sentences[-1]
            # else create a new sentence and save it
            else:
                current_sentence = Sentence(int(row.sent_num))
                sentences.append(current_sentence)
        # if current word hasn't been seen before
        if row.word_index > len(current_sentence.words):
            current_sentence.add_word(row.word_form)
            current_sentence.add_pos(row.pos)
        if row.frame_name != '_':
            current_frame.set_frame_name(row.frame_name)

        if row.lemma_POS != '_':
            current_frame.set_LU(row.lemma_POS, row.word_index)

        if row.FE_Name_BIO != 'O':
            current_frame.add_FE(row.FE_Name_BIO, row.word_index)
    current_sentence.add_frame(current_frame)
    sent_str = [str(sent) for sent in sentences]
    #print('\n'.join(sent_str))


    from jinja2 import Template
    with open('conllvis/template.html.jinja2') as template_fh0:
        template = Template(template_fh0.read())
    with open('conllvis/' + os.path.splitext(sys.argv[1])[0] + '.html', 'w') as html_fh:
        html_fh.write(template.render(stylesheet_name='styles/' + os.path.splitext(sys.argv[1])[0] + '.css',
                        title=os.path.splitext(sys.argv[0]),
                        sentences=sentences))
    with open('conllvis/styles/template.css.jinja2') as template_fh1:
        template1 = Template(template_fh1.read())
    with open('conllvis/styles/' + os.path.splitext(sys.argv[1])[0] + '.css', 'w') as css_fh:
        css_fh.write(template1.render(sentences=sentences))
else:
    print("Invalid number of arguments")
