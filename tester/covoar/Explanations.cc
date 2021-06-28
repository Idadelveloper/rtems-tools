/*! @file Explanations.cc
 *  @brief Explanations Implementation
 *
 *  This file contains the implementation of the functions
 *  which provide a base level of functionality of a Explanations.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <fstream>

#include <rld.h>

#include "Explanations.h"
#include "app_common.h"

namespace Coverage {

  Explanations::Explanations()
  {
  }

  Explanations::~Explanations()
  {
  }

  void Explanations::load(
    const char* const explanations
  )
  {
    #define MAX_LINE_LENGTH 512
    std::ifstream  explain;
    Explanation    e;
    int            line = 1;

    if (!explanations)
      return;

    explain.open( explanations );
    if (!explain) {
      std::ostringstream what;
      what << "Unable to open " << explanations;
      throw rld::error( what, "Explanations::load" );
    }

    while ( 1 ) {
      // Read the starting line of this explanation and
      // skip blank lines between
      do {
        inputBuffer[0] = '\0';
        explain.getline( inputBuffer, MAX_LINE_LENGTH );
        if (explain.fail()) {
          return;
        }
        line++;
      } while ( inputBuffer[0] == '\0' );

      // Have we already seen this one?
      if (set.find( inputBuffer ) != set.end()) {
        std::ostringstream what;
        what << "line " << line
             << "contains a duplicate explanation ("
             << inputBuffer << ")";
        throw rld::error( what, "Explanations::load" );
      }

      // Add the starting line and file
      e.startingPoint = std::string(inputBuffer);
      e.found = false;

      // Get the classification
      explain.getline( inputBuffer, MAX_LINE_LENGTH );
      if (explain.fail()) {
        std::ostringstream what;
        what << "line " << line
             << "out of sync at the classification";
        throw rld::error( what, "Explanations::load" );
      }
      e.classification = inputBuffer;
      line++;

      // Get the explanation
      for (std::string input_line; std::getline( explain, input_line ); ) {
        line++;

        const std::string delimiter = "+++";
        if (input_line.compare( delimiter ) == 0) {
          break;
        }
        // XXX only taking last line.  Needs to be a vector
        e.explanation.push_back( input_line );
      }

      if (explain.fail()) {
        std::ostringstream what;
        what << "line " << line
              << "out of sync at the explanation";
        throw rld::error( what, "Explanations::load" );
      }

      // Add this to the set of Explanations
      set[ e.startingPoint ] = e;
    }

    #undef MAX_LINE_LENGTH
  }

  const Explanation *Explanations::lookupExplanation(
    const std::string& start
  )
  {
    if (set.find( start ) == set.end()) {
      #if 0
        std::cerr << "Warning: Unable to find explanation for "
                  << start << std::endl;
      #endif
      return NULL;
    }
    set[ start ].found = true;
    return &set[ start ];
  }

  void Explanations::writeNotFound(
    const char* const fileName
  )
  {
    std::ofstream notFoundFile;
    bool  notFoundOccurred = false;

    if (!fileName)
      return;

    notFoundFile.open( fileName );
    if (!notFoundFile) {
      std::ostringstream what;
      what << "Unable to open " << fileName
           << " out of sync at the explanation";
      throw rld::error( what, "Explanations::writeNotFound" );
    }

    for (std::map<std::string, Explanation>::iterator itr = set.begin();
         itr != set.end();
         itr++) {
      Explanation e = (*itr).second;
      std::string key = (*itr).first;

      if (!e.found) {
        notFoundOccurred = true;
        notFoundFile << e.startingPoint << std::endl;
      }
    }

    if (!notFoundOccurred) {
      if (!unlink( fileName )) {
        std::cerr << "Warning: Unable to unlink " << fileName
                  << std::endl
                  << std::endl;
      }
    }
  }

}
